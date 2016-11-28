from __future__ import unicode_literals

import StringIO
import tempfile
import zipfile

from datetime import datetime

import requests

from django.db import models

BUILD_STATUSES = (
    ('queued', 'Queued'),
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
    repo = models.ForeignKey('github.Repository', related_name='builds')
    branch = models.ForeignKey('github.Branch', related_name='builds', null=True, blank=True)
    commit = models.CharField(max_length=64)
    tag = models.CharField(max_length=255, null=True, blank=True)
    pr = models.IntegerField(null=True, blank=True)
    trigger = models.ForeignKey('trigger.Trigger', related_name='builds')
    log = models.TextField(null=True, blank=True)
    status = models.CharField(max_length=16, choices=BUILD_STATUSES, default='queued')
    current_flow_index = models.IntegerField(default=0)
    time_queue = models.DateTimeField(auto_now_add=True)
    time_start = models.DateTimeField(null=True, blank=True)
    time_end = models.DateTimeField(null=True, blank=True) 

    def __unicode__(self):
        return '{}: {} - {}'.format(self.id, self.repo, self.commit)

    def run(self):
        self.set_running_status()

        flows = [flow.strip() for flow in self.trigger.flows.split(',')]
        for flow in flows:
            build_flow = BuildFlow(
                build = self,
                flow = flow,
            )
            build_flow.save()
            build_flow.run()
        self.status = 'success'
        self.save()
                
        
        

    def set_running_status(self): 
        self.status = 'running'
        self.time_start = datetime.now()
        self.log += '-- Running flow: {}\n'.format(self.flow)
        self.save()

class BuildFlows(models.Model):
    build = models.ForeignKey('build.Build', related_name='steps')
    status = models.CharField(max_length=16, choices=BUILD_FLOW_STATUSES, default='queued')
    flow = models.CharField(max_length=255, null=True, blank=True)
    log = models.TextField(null=True, blank=True)
    time_queue = models.DateTimeField(auto_now_add=True)
    time_start = models.DateTimeField(null=True, blank=True)
    time_end = models.DateTimeField(null=True, blank=True) 

    def run(self):
        # Record the start
        self.set_running_status()

        # Extract the repo to a temp build dir
        build_dir = self.checkout()

        # Initialize the project config
        project_config = self.get_project_config(build_dir)

        # Look up the org
        org_config = self.get_org(project_config)

        # Run the flow
        result = self.run_flow(project_config, org_config)

        # Record result
        self.record_result(result)
        
       
    def set_running_status(self): 
        self.status = 'running'
        self.time_start = datetime.now()
        self.log += '-- Running flow: {}\n'.format(self.flow)
        self.save()

    def checkout(self):
        zip_url = '{}/archive/{}.zip'.format(
            self.build.repo.url,
            self.build.commit,
        )
        self.log += '-- Download commit from Github URL:\n     {}\n'.format(zip_url)
        self.save()
        resp = requests.get(zip_url)
        build_dir = tempfile.mkdtemp()
        self.log += '-- Extracting zip to temp dir:\n     {}\n'.format(build_dir)
        self.save()
        zip_content = StringIO.StringIO(resp.content)
        zip_file = zipfile.ZipFile(resp.content)
        zip_file.extractall(build_dir)
        build_dir += '/{}-{}'.format(self.build.repo.name, self.build.commit)
        self.log += '-- Commit extracted to build dir:\n     {}\n'.format(build_dir)
        self.save()

    def get_project_config(self, build_dir):
        pass

    def get_org(self, project_config):
        pass

    def run_flow(self, project_config, org_config):
        pass

    def record_result(self, result):
        pass
