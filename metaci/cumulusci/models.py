from __future__ import unicode_literals

import json
import os

from cumulusci.core.config import ScratchOrgConfig
from cumulusci.core.config import OrgConfig
from cumulusci.core.exceptions import ScratchOrgException
from django.core.cache import cache
from django.db import models
from django.conf import settings
from django.urls import reverse
from django.utils import timezone

from model_utils.managers import QueryManager

import choices


class Org(models.Model):
    name = models.CharField(max_length=255)
    json = models.TextField()
    scratch = models.BooleanField(default=False)
    repo = models.ForeignKey('repository.Repository', related_name='orgs')

    # orgmart attributes
    description = models.TextField(null=True, blank=True)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='registered_orgs',
        null=True,
        blank=True
    )
    supertype = models.CharField(
        max_length=50,
        choices=choices.SUPERTYPE_CHOICES,
        default=choices.SUPERTYPE_CI
    )
    org_type = models.CharField(
        max_length=50,
        choices=choices.ORGTYPE_CHOICES,
        default=choices.ORGTYPE_PRODUCTION
    )
    last_deploy = models.DateTimeField(null=True, blank=True)
    last_deploy_version = models.CharField(max_length=255, null=True, blank=True)
    release_cycle = models.CharField(
        max_length=50,
        choices=choices.RELEASE_CHOICES,
        null=True,
        blank=True
    )

    objects = models.Manager()
    ci_orgs = QueryManager(supertype=choices.SUPERTYPE_CI)
    registered_orgs = QueryManager(supertype=choices.SUPERTYPE_REGISTERED)

    class Meta:
        ordering = ['name', 'repo__owner', 'repo__name']

    def __unicode__(self):
        return '{}: {}'.format(self.repo.name, self.name)

    def get_absolute_url(self):
        return reverse('org_detail', kwargs={'org_id': self.id})

    def get_org_config(self):
        org_config = json.loads(self.json)

        return OrgConfig(org_config)

    @property
    def lock_id(self):
        if not self.scratch:
            return u'metaci-org-lock-{}'.format(self.id)

    @property
    def is_locked(self):
        if not self.scratch:
            return True if cache.get(self.lock_id) else False

    def lock(self):
        if not self.scratch:
            cache.add(self.lock_id, 'manually locked', timeout=None)

    def unlock(self):
        if not self.scratch:
            cache.delete(self.lock_id)


class ScratchOrgInstance(models.Model):
    org = models.ForeignKey('cumulusci.Org', related_name='instances')
    build = models.ForeignKey('build.Build', related_name='scratch_orgs', null=True, blank=True)
    username = models.CharField(max_length=255)
    sf_org_id = models.CharField(max_length=32)
    deleted = models.BooleanField(default=False)
    delete_error = models.TextField(null=True, blank=True)
    json = models.TextField()
    json_dx = models.TextField()
    time_created = models.DateTimeField(auto_now_add=True)
    time_deleted = models.DateTimeField(null=True, blank=True)

    def __unicode__(self):
        if self.username:
            return self.username
        if self.sf_org_id:
            return self.sf_org_id
        return '{}: {}'.format(self.org, self.id)

    def get_absolute_url(self):
        return reverse('org_instance_detail', kwargs={'org_id': self.org.id, 'instance_id': self.id})

    def get_org_config(self):
        # Write the org json file to the filesystem for Salesforce DX to use
        dx_local_dir = os.path.join(os.path.expanduser('~'), '.local', '.sfdx')
        if not os.path.isdir(dx_local_dir):
            dx_local_dir = os.path.join(os.path.expanduser('~'), '.sfdx')
        filename = os.path.join(dx_local_dir, '{}.json'.format(self.username))
        with open(filename, 'w') as f:
            f.write(self.json_dx)

        org_config = json.loads(self.json)

        return ScratchOrgConfig(org_config)

    def delete_org(self, org_config=None):
        if org_config is None:
            org_config = self.get_org_config()

        try:
            org_config.delete_org()
        except ScratchOrgException as e:
            self.delete_error = e.message
            self.deleted = False
            self.save()
            return

        self.time_deleted = timezone.now()
        self.deleted = True
        self.save()


class Service(models.Model):
    name = models.CharField(max_length=255)
    json = models.TextField()

    def __unicode__(self):
        return self.name
