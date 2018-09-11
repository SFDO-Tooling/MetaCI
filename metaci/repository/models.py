from __future__ import unicode_literals

from django.db import models
from django.urls import reverse

from github3 import login
from django.conf import settings
from model_utils.models import SoftDeletableModel

class Repository(models.Model):
    name = models.CharField(max_length=255)
    owner = models.CharField(max_length=255)
    github_id = models.IntegerField(null=True, blank=True)
    url = models.URLField(max_length=255)
    public = models.BooleanField(default=True)

    release_tag_regex = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        ordering = ['name','owner']
        verbose_name_plural = 'repositories'

    def get_absolute_url(self):
        return reverse('repo_detail', kwargs={'owner': self.owner, 'name': self.name})

    def __unicode__(self):
        return '{}/{}'.format(self.owner, self.name)
   
    @property 
    def github_api(self):
        gh = login(settings.GITHUB_USERNAME, settings.GITHUB_PASSWORD)
        repo = gh.repository(self.owner, self.name)
        return repo
        
class Branch(SoftDeletableModel):
    name = models.CharField(max_length=255)
    repo = models.ForeignKey(Repository, related_name='branches', on_delete=models.CASCADE)

    class Meta:
        ordering = ['repo__name','repo__owner', 'name']
        verbose_name_plural = 'branches'

    def get_absolute_url(self):
        return reverse('branch_detail', kwargs={'owner': self.repo.owner, 'name': self.repo.name, 'branch': self.name})

    def __unicode__(self):
        return u'{}'.format(self.name)

    @property 
    def github_api(self):
        branch = self.repo.github_api.branch(self.name)
        return branch
