from __future__ import unicode_literals

from django.db import models
from django.urls import reverse


class Repository(models.Model):
    name = models.CharField(max_length=255)
    owner = models.CharField(max_length=255)
    github_id = models.IntegerField(null=True, blank=True)
    url = models.URLField(max_length=255)
    public = models.BooleanField(default=True)

    class Meta:
        ordering = ['name','owner']

    def get_absolute_url(self):
        return reverse('repo_detail', kwargs={'owner': self.owner, 'name': self.name})

    def __unicode__(self):
        return '{}/{}'.format(self.owner, self.name)
    
class Branch(models.Model):
    name = models.CharField(max_length=255)
    repo = models.ForeignKey(Repository, related_name='branches')
    deleted = models.BooleanField(default=False)

    class Meta:
        ordering = ['repo__name','repo__owner', 'name']

    def get_absolute_url(self):
        return reverse('branch_detail', kwargs={'owner': self.repo.owner, 'name': self.repo.name, 'branch': self.name})

    def __unicode__(self):
        return u'[{}] {}'.format(self.repo.name, self.name)
