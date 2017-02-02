from __future__ import unicode_literals

from django.db import models

class Org(models.Model):
    name = models.CharField(max_length=255)
    json = models.TextField()
    scratch = models.BooleanField(default=False)
    repo = models.ForeignKey('repository.Repository', related_name='orgs')

    class Meta:
        ordering = ['name', 'repo__owner', 'repo__name']

    def __unicode__(self):
        return '{}: {}'.format(self.repo.name, self.name)

class ScratchOrgInstance(models.Model):
    org = models.ForeignKey('cumulusci.Org', related_name='instances')
    username = models.CharField(max_length=255)
    sf_org_id = models.CharField(max_length=32)
    deleted = models.BooleanField(default=False)
    json = models.TextField()
    json_dx = models.TextField()
    time_created = models.DateTimeField(auto_now_add=True)
    time_deleted = models.DateTimeField(null=True, blank=True)

class Service(models.Model):
    name = models.CharField(max_length=255)
    json = models.TextField()

    def __unicode__(self):
        return self.name
