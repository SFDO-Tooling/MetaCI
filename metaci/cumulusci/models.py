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
from django.core.exceptions import ValidationError

from model_utils.managers import QueryManager

import choices


class Org(models.Model):
    name = models.CharField(max_length=255)
    json = models.TextField()

    repo = models.ForeignKey('repository.Repository', related_name='orgs')

    org_id = models.CharField(max_length=18, blank=True, null=True)

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
    push_schedule = models.CharField(
        max_length=50,
        choices=choices.PUSHSCHEDULE_CHOICES,
        null=True,
        blank=True
    )

    class Meta:
        ordering = ['name', 'repo__owner', 'repo__name']
        unique_together = ('repo', 'name')

    objects = models.Manager() # first manager declared on model is the one used by admin etc
    ci_orgs = QueryManager(supertype=choices.SUPERTYPE_CI)
    registered_orgs = QueryManager(supertype=choices.SUPERTYPE_REGISTERED)


    def __unicode__(self):
        return '{}: {}'.format(self.repo.name, self.name)

    def get_absolute_url(self):
        return reverse('org_detail', kwargs={'org_id': self.id})

    def get_org_config(self):
        if self.supertype is not choices.SUPERTYPE_CI:
            raise RuntimeError('Org is not a CI org and does not have an OrgConfig.')

        org_config = json.loads(self.json)

        return OrgConfig(org_config)

    @property
    def scratch(self):
        return self.org_type == choices.ORGTYPE_SCRATCH

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

    def clean(self):
        errors = {}
        if not self.scratch and not self.org_id:
            errors['org_id'] = 'Org ID is required for non-scratch orgs.'

        if self.supertype == choices.SUPERTYPE_CI:
            try:
                obj = json.loads(self.json)
            except (TypeError, ValueError), e:
                errors['json'] = 'OrgConfig invalid: {}'.format(e)
                raise ValidationError(errors) #exit fast if its bad JSON.

            if self.scratch and 'config_file' not in obj:
                errors['json'] = 'Scratch org JSON must contain a config_file.' 

            if not self.scratch and 'id' not in obj:
                errors['json'] = 'Persistent org expected to have an id in its JSON!'
        
        if errors: 
            raise ValidationError(errors)


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
