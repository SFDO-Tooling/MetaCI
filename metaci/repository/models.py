from __future__ import unicode_literals

from cumulusci.core.github import get_github_api
from django.apps import apps
from django.conf import settings
from django.db import models
from django.http import Http404
from django.urls import reverse
from model_utils.models import SoftDeletableModel

class RepositoryQuerySet(models.QuerySet):
    def for_user(self, user, perms=None):
        if user.is_superuser:
            return self
        if perms is None:
            perms = 'plan.view_builds'
        PlanRepository = apps.get_model('plan.PlanRepository')
        return self.filter(
            planrepository__in = PlanRepository.objects.for_user(user, perms),
        ).distinct()

    def get_for_user_or_404(self, user, query, perms=None):
        try:
            return self.for_user(user, perms).get(**query)
        except Repository.DoesNotExist:
            raise Http404

class Repository(models.Model):
    name = models.CharField(max_length=255)
    owner = models.CharField(max_length=255)
    github_id = models.IntegerField(null=True, blank=True)
    url = models.URLField(max_length=255)

    release_tag_regex = models.CharField(max_length=255, blank=True, null=True)

    objects = RepositoryQuerySet.as_manager()

    class Meta:
        ordering = ['name','owner']
        verbose_name_plural = 'repositories'

    def get_absolute_url(self):
        return reverse('repo_detail', kwargs={'owner': self.owner, 'name': self.name})

    def __unicode__(self):
        return '{}/{}'.format(self.owner, self.name)
   
    @property 
    def github_api(self):
        gh = get_github_api(settings.GITHUB_USERNAME, settings.GITHUB_PASSWORD)
        repo = gh.repository(self.owner, self.name)
        return repo

    @property
    def latest_release(self):
        try:
            return self.releases.latest()
        except Repository.DoesNotExist:
            return None
        
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
