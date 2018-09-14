from __future__ import unicode_literals
import re
import yaml

from django.apps import apps
from django.db import models
from django.urls import reverse
from django.core.exceptions import ValidationError

from metaci.repository.models import Repository


TRIGGER_TYPES = (
    ('manual', 'Manual'),
    ('commit', 'Commit'),
    ('tag', 'Tag'),
    ('org', 'Org Request'),
    ('qa', 'QA Testing'),
)

DASHBOARD_CHOICES = (
    ('last', 'Most Recent Build'),
    ('recent', '5 Most Recent Build'),
    ('branches', 'Latest Builds by Branch'),
)

def validate_yaml_field(value):
    try:
        yaml.safe_load(value)
    except yaml.YAMLError as err:
        raise ValidationError('Error parsing additional YAML: {}'.format(err))


class Plan(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)
    repos = models.ManyToManyField(
        Repository,
        related_name='plans',
        through='PlanRepository',
        through_fields=('plan', 'repo'),
    )
    type = models.CharField(max_length=8, choices=TRIGGER_TYPES)
    regex = models.CharField(max_length=255, null=True, blank=True)
    flows = models.CharField(max_length=255)
    org = models.CharField(max_length=255)
    context = models.CharField(max_length=255, null=True, blank=True)
    public = models.BooleanField(default=True)
    active = models.BooleanField(default=True)
    dashboard = models.CharField(max_length=8, choices=DASHBOARD_CHOICES, default=None, null=True, blank=True)
    junit_path = models.CharField(max_length=255, null=True, blank=True)
    sfdx_config = models.TextField(null=True, blank=True)
    yaml_config = models.TextField(null=True, blank=True, validators=[validate_yaml_field])

    class Meta:
        ordering = ['name', 'active', 'context']

    def get_absolute_url(self):
        return reverse('plan_detail', kwargs={'plan_id': self.id})

    def __unicode__(self):
        return self.name

    def get_repos(self):
        for repo in self.repos.all():
            yield repo

    def check_push(self, push):
        run_build = False
        commit = None
        commit_message = None

        # Handle commit events
        if self.type == 'commit':
            # Check if the event was triggered by a commit
            if not push['ref'].startswith('refs/heads/'):
                return run_build, commit, commit_message
            branch = push['ref'][11:]

            # Check the branch against regex
            if not re.match(self.regex, branch):
                return run_build, commit, commit_message

            run_build = True
            commit = push['after']
            if commit == '0000000000000000000000000000000000000000':
                run_build = False
                commit = None
                return run_build, commit, commit_message

            for commit_info in push.get('commits',[]):
                if commit_info['id'] == commit:
                    commit_message = commit_info['message']
                    break
   
            # Skip build if commit message contains [ci skip] 
            if commit_message and '[ci skip]' in commit_message:
                run_build = False
                commit = None
            return run_build, commit, commit_message
                

        # Handle tag events
        elif self.type == 'tag':
            # Check if the event was triggered by a tag
            if not push['ref'].startswith('refs/tags/'):
                return run_build, commit, commit_message
            tag = push['ref'][10:]
            
            # Check the tag against regex
            if not re.match(self.regex, tag):
                return run_build, commit, commit_message
   
            if push['head_commit']:
                # Skip... for some reason a second push event is sent that has no 'before' but does have a head_commit 
                return run_build, commit, commit_message

            run_build = True
            commit = push['before']
            return run_build, commit, commit_message
    
        return run_build, commit, commit_message


class PlanRepositoryManager(models.Manager):
    def get_queryset(self):
        return super(PlanRepositoryManager, self).get_queryset().annotate(
            alive=models.ExpressionWrapper(
                models.Q(active=True) & models.Q(plan__active=True),
                output_field=models.BooleanField()
            )
        )

class PlanRepository(models.Model):
    plan = models.ForeignKey(Plan, on_delete=models.CASCADE)
    repo = models.ForeignKey(Repository, on_delete=models.CASCADE)
    active = models.BooleanField(default=True)
    
    objects = PlanRepositoryManager()

    class Meta:
        ordering = ['repo', 'plan']
        verbose_name_plural = 'Plan Repositories'
        #unique_together = ('plan', 'repo')

    def __unicode__(self):
        return u'[{}] {}'.format(self.repo, self.plan)

    def get_absolute_url(self):
        return reverse(
            "plan_detail_repo",
            kwargs={
                "plan_id": self.plan.id,
                "repo_owner": self.repo.owner,
                "repo_name": self.repo.name,
            },
        )

    @property
    def alive(self):
        if self._alive is not None:
            return self._alive # if we came from the default manager, this is already calculated.
        else:
            return (self.active and self.plan.active)
    
    @alive.setter
    def alive(self, val):
        # figure out to only allow this from the query set?
        self._alive = val

