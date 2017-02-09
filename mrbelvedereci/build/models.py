from __future__ import unicode_literals

import StringIO
import json
import os
import re
import shutil
import sys
import tempfile
import zipfile

from django.utils import timezone

import requests

from django.conf import settings
from django.db import models
from django.urls import reverse

from mrbelvedereci.build.utils import format_log
from mrbelvedereci.cumulusci.config import MrbelvedereGlobalConfig
from mrbelvedereci.cumulusci.config import MrbelvedereProjectConfig
from mrbelvedereci.cumulusci.keychain import MrbelvedereProjectKeychain
from mrbelvedereci.cumulusci.logger import init_logger
from mrbelvedereci.testresults.importer import import_test_results

from cumulusci.core.config import FlowConfig
from cumulusci.core.exceptions import ApexTestException
from cumulusci.salesforce_api.exceptions import MetadataComponentFailure
from cumulusci.core.exceptions import FlowNotFoundError
from cumulusci.core.utils import import_class

BUILD_STATUSES = (
    ('queued', 'Queued'),
    ('waiting', 'Waiting'),
    ('running', 'Running'),
    ('success', 'Success'),
    ('error', 'Error'),
    ('fail', 'Failed'),
)
BUILD_FLOW_STATUSES = (
    ('queued', 'Queued'),
    ('running', 'Running'),
    ('success', 'Success'),
    ('error', 'Error'),
    ('fail', 'Failed'),
)

class Build(models.Model):
    repo = models.ForeignKey('repository.Repository', related_name='builds')
    branch = models.ForeignKey('repository.Branch', related_name='builds', null=True, blank=True)
    commit = models.CharField(max_length=64)
    commit_message = models.TextField(null=True, blank=True)
    tag = models.CharField(max_length=255, null=True, blank=True)
    pr = models.IntegerField(null=True, blank=True)
    plan = models.ForeignKey('plan.Plan', related_name='builds')
    org = models.ForeignKey('cumulusci.Org', related_name='builds', null=True, blank=True)
    org_instance = models.ForeignKey('cumulusci.ScratchOrgInstance', related_name='builds', null=True, blank=True)
    log = models.TextField(null=True, blank=True)
    exception = models.TextField(null=True, blank=True)
    error_message = models.TextField(null=True, blank=True)
    status = models.CharField(max_length=16, choices=BUILD_STATUSES, default='queued')
    keep_org = models.BooleanField(default=False)
    task_id_status_start = models.CharField(max_length=64, null=True, blank=True)
    task_id_check = models.CharField(max_length=64, null=True, blank=True)
    task_id_run = models.CharField(max_length=64, null=True, blank=True)
    task_id_status_end = models.CharField(max_length=64, null=True, blank=True)
    current_rebuild = models.ForeignKey('build.Rebuild', related_name='current_builds', null=True, blank=True)
    time_queue = models.DateTimeField(auto_now_add=True)
    time_start = models.DateTimeField(null=True, blank=True)
    time_end = models.DateTimeField(null=True, blank=True) 

    class Meta:
        ordering = ['-time_queue']

    def __unicode__(self):
        return '{}: {} - {}'.format(self.id, self.repo, self.commit)

    def get_log_html(self):
        if self.log:
            return format_log(self.log)

    def get_absolute_url(self):
        return reverse('build_detail', kwargs={'build_id': str(self.id)})

    def get_external_url(self):
        url = '{}{}'.format(settings.SITE_URL, self.get_absolute_url())
        return url

    def run(self):
        self.logger = init_logger(self)
        self.set_running_status()

        try:
            # Extract the repo to a temp build dir
            self.build_dir = self.checkout()
    
            # Change directory to the build_dir
            os.chdir(self.build_dir)
    
            # Initialize the project config
            project_config = self.get_project_config()
    
            # Look up the org
            org_config = self.get_org(project_config)
    
        except Exception as e:
            self.logger.error(unicode(e))
            self.status = 'error'
            self.time_end = timezone.now()
            self.save()
            self.delete_build_dir()
            if self.current_rebuild:
                self.current_rebuild.status = self.status
                self.current_rebuild.time_end = timezone.now()
                self.current_rebuild.save()
            return
      
        # Run flows
        try:
            flows = [flow.strip() for flow in self.plan.flows.split(',')]
            for flow in flows:
                self.logger = init_logger(self)
                self.logger.info('Running flow: {}'.format(flow))
                self.save()
    
                build_flow = BuildFlow(
                    build = self,
                    rebuild = self.current_rebuild,
                    flow = flow,
                )
                build_flow.save()
                build_flow.run(project_config, org_config)
    
                if build_flow.status != 'success':
                    self.logger = init_logger(self)
                    self.logger.error('Build flow {} completed with status {}'.format(flow, build_flow.status))
                    self.logger.error('    {}: {}'.format(build_flow.exception, build_flow.error_message))
                    self.status = build_flow.status
                    self.exception = build_flow.exception
                    self.error_message = build_flow.error_message
                    self.time_end = timezone.now()
                    self.save()
                    if org_config.created:
                        self.delete_org(org_config)
                    if self.current_rebuild:
                        self.current_rebuild.status = self.status
                        self.current_rebuild.time_end = timezone.now()
                        self.current_rebuild.save()
                    return
                else:
                    self.logger = init_logger(self)
                    self.logger.info('Build flow {} completed successfully'.format(flow))
                    self.save()
    
        except Exception as e:
            if org_config.created:
                self.delete_org(org_config)
            self.logger = init_logger(self)
            self.logger.error(unicode(e))
            self.status = 'error'
            self.time_end = timezone.now()
            self.save()
            self.delete_build_dir()
            if self.current_rebuild:
                self.current_rebuild.status = self.status
                self.current_rebuild.time_end = timezone.now()
                self.current_rebuild.save()
            return

        if org_config.created:
            self.delete_org(org_config)

        self.delete_build_dir()

        # Set success status
        self.status = 'success'
        self.time_end = timezone.now()
        self.save()
        if self.current_rebuild:
            self.current_rebuild.status = self.status
            self.current_rebuild.time_end = timezone.now()
            self.current_rebuild.save()

    def set_running_status(self): 
        self.status = 'running'
        self.time_start = timezone.now()
        self.logger.info('-- Building commit {}'.format(self.commit))
        self.save()
        if self.current_rebuild:
            self.current_rebuild.status = self.status
            self.current_rebuild.time_start = timezone.now()
            self.current_rebuild.save()

    def checkout(self):
        zip_url = '{}/archive/{}.zip'.format(
            self.repo.url,
            self.commit,
        )
        self.logger.info('-- Download commit from URL: {}'.format(zip_url))
        self.save()
        kwargs = {'auth': (settings.GITHUB_USERNAME, settings.GITHUB_PASSWORD)}
        resp = requests.get(zip_url, **kwargs)
        build_dir = tempfile.mkdtemp()
        self.logger.info('-- Extracting zip to temp dir {}'.format(build_dir))
        self.save()
        zip_content = StringIO.StringIO(resp.content)
        zip_file = zipfile.ZipFile(zip_content)
        zip_file.extractall(build_dir)
        build_dir += '/{}-{}'.format(self.repo.name, self.commit)
        self.logger.info('-- Commit extracted to build dir: {}'.format(build_dir))
        self.save()
        return build_dir

    def get_project_config(self):
        global_config = MrbelvedereGlobalConfig()
        project_config = global_config.get_project_config(self)
        keychain = MrbelvedereProjectKeychain(project_config, None, self)
        project_config.set_keychain(keychain)
        return project_config

    def get_org(self, project_config):
        org_config = project_config.keychain.get_org(self.plan.org)
        self.org = org_config.org
        self.org_instance = org_config.org_instance
        self.save()
        return org_config

    def delete_org(self, org_config):
        self.logger = init_logger(self)
        if not org_config.scratch:
            return
        if self.keep_org:
            self.logger.info('Skipping scratch org deletion since keep_org was requested')
            return
        try:
            self.org_instance.delete_org(org_config)
        except Exception as e:
            self.logger.error(e.message)
            self.save()

    def delete_build_dir(self):
        if hasattr(self, 'build_dir'):
            self.logger.info('Deleting build dir {}'.format(self.build_dir))
            shutil.rmtree(self.build_dir)
            self.save()

class BuildFlow(models.Model):
    build = models.ForeignKey('build.Build', related_name='flows')
    rebuild = models.ForeignKey('build.Rebuild', related_name='flows', null=True, blank=True)
    status = models.CharField(max_length=16, choices=BUILD_FLOW_STATUSES, default='queued')
    flow = models.CharField(max_length=255, null=True, blank=True)
    log = models.TextField(null=True, blank=True)
    exception = models.TextField(null=True, blank=True)
    error_message = models.TextField(null=True, blank=True)
    time_queue = models.DateTimeField(auto_now_add=True)
    time_start = models.DateTimeField(null=True, blank=True)
    time_end = models.DateTimeField(null=True, blank=True) 
    tests_total = models.IntegerField(null=True, blank=True)
    tests_pass = models.IntegerField(null=True, blank=True)
    tests_fail = models.IntegerField(null=True, blank=True)
    
    def __unicode__(self):
        return '{}: {} - {} - {}'.format(self.build.id, self.build.repo, self.build.commit, self.flow)

    def get_absolute_url(self):
        return reverse('build_detail', kwargs={'build_id': str(self.build.id)}) + '#flow-{}'.format(self.flow)

    def get_log_html(self):
        if self.log:
            return format_log(self.log)

    def run(self, project_config, org_config):
        # Record the start
        self.set_running_status()

        # Set up logger
        self.logger = init_logger(self)

        exception = None
        try:
            # Run the flow
            result = self.run_flow(project_config, org_config)

            # Load test results
            self.load_test_results()

            # Record result
            self.record_result()

        except MetadataComponentFailure as e:
            exception = e
            self.status = 'fail'

        except ApexTestException as e:
            exception = e
            self.load_test_results()
            self.status = 'fail'

        except Exception as e:
            exception = e
            self.status = 'error'

        if exception:
            if self.status == 'error':
                self.logger.error(unicode(e))
            self.exception = e.__class__.__name__
            self.error_message = unicode(e)
            self.time_end = timezone.now()
            self.save()

    def set_running_status(self): 
        self.status = 'running'
        self.time_start = timezone.now()
        self.save()

    def run_flow(self, project_config, org_config):
        # Add the repo root to syspath to allow for custom tasks and flows in the repo
        sys.path.append(project_config.repo_root)

        flow = getattr(project_config, 'flows__{}'.format(self.flow))
        if not flow:
            raise FlowNotFoundError('Flow not found: {}'.format(self.flow))
        flow_config = FlowConfig(flow)
    
        # Get the class to look up options
        class_path = flow_config.config.get('class_path', 'cumulusci.core.flows.BaseFlow')
        flow_class = import_class(class_path)
    
        # Create the flow and handle initialization exceptions
        self.flow_instance = flow_class(project_config, flow_config, org_config)

        # Run the flow
        res = self.flow_instance()

        return res
    
    def record_result(self):
        self.status = 'success'
        self.time_end = timezone.now()
        self.save()

    def load_test_results(self):
        if not os.path.isfile('test_results.json'):
            return
        
        f = open('test_results.json', 'r')
        results = json.load(f)
        import_test_results(self, results)

        self.tests_total = self.test_results.count()
        self.tests_pass = self.test_results.filter(outcome = 'Pass').count()
        self.tests_fail = self.test_results.filter(outcome__in = ['Fail','CompileFail']).count()
        self.save()

class Rebuild(models.Model):
    build = models.ForeignKey('build.Build', related_name='rebuilds')
    user = models.ForeignKey('users.User', related_name='rebuilds')
    status = models.CharField(max_length=16, choices=BUILD_STATUSES, default='queued')
    time_queue = models.DateTimeField(auto_now_add=True)
    time_start = models.DateTimeField(null=True, blank=True)
    time_end = models.DateTimeField(null=True, blank=True) 
