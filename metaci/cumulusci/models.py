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
from django.contrib.contenttypes.models import ContentType

from model_utils.managers import QueryManager
from model_utils.choices import Choices

import choices


class AdminEntryManager(models.Manager):
    use_in_migrations = True

    def log(self, user_id, org_id, change_message, action_flag=None, related_object=None):
        if isinstance(change_message, list):
            change_message = json.dumps(change_message)
        log_obj = self.model(
            user_id=user_id,
            org_id=org_id,
            change_message=change_message,
            action_flag=action_flag,
            action_time=timezone.now()
        )
        if related_object:
            log_obj.related_object_object_id = related_object.id
        
        log_obj.save()
        return log_obj
    
    
class OrgAdminAction(models.Model):
    # Attributes
    ## who
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        models.PROTECT,
    )
    ## what
    change_message = models.TextField()
    action_flag = models.CharField(
        choices=choices.ORG_ACTION_FLAGS, 
        default=choices.ORG_ACTION_FLAGS.other, 
        max_length=20
    )
    ## when
    action_time = models.DateTimeField(
        default=timezone.now,
        editable=False,
    )
    ## where
    org = models.ForeignKey('cumulusci.Org', models.PROTECT, related_name='admin_actions')
    ## with
    related_object_content_type = models.ForeignKey(
        ContentType,
        models.SET_NULL,
        blank=True, null=True,
    )
    related_object_object_id = models.TextField(blank=True, null=True)
    related_object_object_repr = models.CharField(max_length=200, blank=True, null=True)
    
    # Managers
    objects = AdminEntryManager()

class Org(models.Model):
    # Identity Fields
    name = models.CharField(max_length=255)
    repo = models.ForeignKey('repository.Repository', related_name='orgs')

    # Common Attributes 
    sf_org_id = models.CharField(max_length=18, blank=True, null=True)
    supertype = models.CharField(
        max_length=50,
        choices=choices.SUPERTYPES,
        default=choices.SUPERTYPES.ci
    )
    description = models.TextField(null=True, blank=True)
    org_type = models.CharField(
        max_length=50,
        choices=choices.ORGTYPES,
        default=choices.ORGTYPES.production
    )

    # CI Orgs
    json = models.TextField()

    # Registered Orgs
    push_schedule = models.CharField(
        max_length=50,
        choices=choices.PUSHSCHEDULES,
        null=True,
        blank=True
    )
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='orgs',
        null=True,
        blank=True
    )

    class Meta:
        ordering = ['name', 'repo__owner', 'repo__name']
        unique_together = ('repo', 'name')
        permissions = choices.ORG_PERMISSIONS

    objects = models.Manager() # first manager declared on model is the one used by admin etc
    ci_orgs = QueryManager(supertype=choices.SUPERTYPES.ci)
    registered_orgs = QueryManager(supertype=choices.SUPERTYPES.registered)

    def __unicode__(self):
        return '{}: {}'.format(self.repo.name, self.name)

    def get_absolute_url(self):
        return reverse('org_detail', kwargs={'org_id': self.id})

    def get_org_config(self):
        if self.supertype is not choices.SUPERTYPES.ci:
            raise RuntimeError('Org is not a CI org and does not have an OrgConfig.')

        org_config = json.loads(self.json)

        return OrgConfig(org_config)

    @property
    def scratch(self):
        return self.org_type == choices.ORGTYPES.scratch

    @property
    def lock_id(self):
        if not self.scratch:
            return u'metaci-org-lock-{}'.format(self.id)

    @property
    def is_locked(self):
        if not self.scratch:
            return True if cache.get(self.lock_id) else False

    def lock(self, request=None):
        if self.scratch:
            return

        cache.add(self.lock_id, 'manually locked', timeout=None)
        
        if request:
            OrgAdminAction.objects.log(
                user_id = request.user.id,
                org_id = self.id,
                change_message = "Manually locked org with lock ID {}".format(self.lock_id),
                action_flag = OrgAdminAction.ACTION_FLAGS.lock
            )
        
    def unlock(self, request=None):
        if self.scratch:
            return
        
        cache.delete(self.lock_id)
    
        if request:
            OrgAdminAction.objects.log(
                user_id = request.user.id,
                org_id = self.id,
                change_message = "Manually unlocked org with lock ID {}".format(self.lock_id),
                action_flag = OrgAdminAction.action_flags.unlock
            )

    def clean(self):
        errors = {}
        if not self.scratch and not self.sf_org_id:
            errors['sf_org_id'] = 'SF Org ID is required for non-scratch orgs.'

        if self.supertype == choices.SUPERTYPES.ci:
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
