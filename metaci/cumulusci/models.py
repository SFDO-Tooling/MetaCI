from __future__ import unicode_literals

import json
import os
from calendar import timegm
from datetime import datetime
from urllib.parse import urljoin

import jwt
import requests
from cumulusci.core.config import ScratchOrgConfig
from cumulusci.core.config import OrgConfig
from cumulusci.core.exceptions import ScratchOrgException
from django.apps import apps
from django.core.cache import cache
from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from django.conf import settings
from guardian.shortcuts import get_objects_for_user
from simple_salesforce import Salesforce as SimpleSalesforce
from simple_salesforce.exceptions import SalesforceError

def jwt_session(url=None, username=None):
    if url is None:
        url = 'https://login.salesforce.com'

    payload = {
        'alg': 'RS256',
        'iss': settings.SFDX_CLIENT_ID,
        'sub': username,
        'aud': url, #jwt aud is NOT mydomain
        'exp': timegm(datetime.utcnow().utctimetuple()),
    }
    encoded_jwt = jwt.encode(
        payload,
        settings.SFDX_HUB_KEY,
        algorithm='RS256',
    )
    data = {
        'grant_type': 'urn:ietf:params:oauth:grant-type:jwt-bearer',
        'assertion': encoded_jwt,
    }
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    auth_url = urljoin(url, 'services/oauth2/token')
    response = requests.post(url=auth_url, data=data, headers=headers)
    response.raise_for_status()

    return response.json()

def sf_session(jwt):
    return SimpleSalesforce(
            instance_url=jwt['instance_url'],
            session_id=jwt['access_token'],
            client_id='metaci',
            version='42.0'
    )

class OrgQuerySet(models.QuerySet):
    def for_user(self, user, perms=None):
        if perms is None:
            perms = 'plan.org_login'
        PlanRepository = apps.get_model('plan.PlanRepository')
        planrepos = PlanRepository.objects.for_user(user, perms)
        planrepos = planrepos.values('plan__org', 'repo')
        q = models.Q()
        for plan_org in planrepos:
            q.add(models.Q(name=plan_org['plan__org'], repo_id=plan_org['repo']), models.Q.OR)
        return self.filter(q)

class Org(models.Model):
    name = models.CharField(max_length=255)
    json = models.TextField()
    scratch = models.BooleanField(default=False)
    repo = models.ForeignKey('repository.Repository', related_name='orgs', on_delete=models.CASCADE)

    objects = OrgQuerySet.as_manager()

    class Meta:
        ordering = ['name', 'repo__owner', 'repo__name']

    def __unicode__(self):
        return '{}: {}'.format(self.repo.name, self.name)

    def get_absolute_url(self):
        return reverse('org_detail', kwargs={'org_id': self.id})

    def get_org_config(self):
        org_config = json.loads(self.json)

        return OrgConfig(org_config, self.name)

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

class ActiveOrgManager(models.Manager):
    def get_queryset(self):
        return super(ActiveOrgManager, self).get_queryset().filter(
            deleted=False, expiration_date__gt=timezone.now()
        )

class ExpiredOrgManager(models.Manager):
    def get_queryset(self):
        return super(ExpiredOrgManager, self).get_queryset().filter(
            deleted=False, expiration_date__lte=timezone.now()
        )

class ScratchOrgInstance(models.Model):
    org = models.ForeignKey('cumulusci.Org', related_name='instances', on_delete=models.CASCADE)
    build = models.ForeignKey('build.Build', related_name='scratch_orgs', null=True, blank=True, on_delete=models.CASCADE)
    username = models.CharField(max_length=255)
    sf_org_id = models.CharField(max_length=32)
    deleted = models.BooleanField(default=False)
    delete_error = models.TextField(null=True, blank=True)
    json = models.TextField()
    time_created = models.DateTimeField(auto_now_add=True)
    time_deleted = models.DateTimeField(null=True, blank=True)
    expiration_date = models.DateTimeField(null=True, blank=True)

    objects = models.Manager() # the first manager is used by admin
    active = ActiveOrgManager()
    expired = ExpiredOrgManager()

    def __unicode__(self):
        if self.username:
            return self.username
        if self.sf_org_id:
            return self.sf_org_id
        return '{}: {}'.format(self.org, self.id)

    def get_absolute_url(self):
        return reverse('org_instance_detail', kwargs={'org_id': self.org.id, 'instance_id': self.id})

    @property
    def days(self):
        return self._get_org_config().days

    @property
    def days_alive(self):
        return self._get_org_config().days_alive

    def get_org_config(self):
        return self._get_org_config()

    def _get_org_config(self):
        org_config = json.loads(self.json)
        org_config['date_created'] = parse_datetime(org_config['date_created'])
        return ScratchOrgConfig(org_config, self.org.name)

    def get_jwt_based_session(self):
        return jwt_session('https://test.salesforce.com', self.username)

    def delete_org(self, org_config=None):
        if org_config is None:
            org_config = self.get_org_config()

        try:
            # connect to SFDX Hub
            sfjwt = jwt_session(username=settings.SFDX_HUB_USERNAME)
            sf = sf_session(sfjwt)
            # query ActiveScratchOrg via OrgId
            asos = sf.query(
                'SELECT ID FROM ActiveScratchOrg WHERE ScratchOrg=\'{}\''.format(self.sf_org_id)
            )
            if asos['totalSize'] > 0:
                aso = asos['records'][0]['Id']
                # delete ActiveScratchOrg
                sf.ActiveScratchOrg.delete(aso)
            else:
                self.delete_error = 'Org did not exist when deleted.'
        except SalesforceError as e:
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
