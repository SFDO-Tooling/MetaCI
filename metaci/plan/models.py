from __future__ import unicode_literals
import re
import yaml

from django.apps import apps
from django.db import models
from django.http import Http404
from django.urls import reverse
from django.core.exceptions import ValidationError
from guardian.shortcuts import get_objects_for_user

from metaci.repository.models import Repository


TRIGGER_TYPES = (("manual", "Manual"), ("commit", "Commit"), ("tag", "Tag"))

BUILD_ROLES = (
    ("beta_release", "Beta Release"),
    ("beta_test", "Beta Test"),
    ("deploy", "Deployment"),
    ("feature", "Feature Test"),
    ("feature_robot", "Feature Test Robot"),
    ("other", "Other"),
    ("qa", "QA Org"),
    ("release_deploy", "Release Deploy"),
    ("release", "Release"),
    ("release_test", "Release Test"),
    ("scratch", "Scratch Org"),
)

DASHBOARD_CHOICES = (
    ("last", "Most Recent Build"),
    ("recent", "5 Most Recent Build"),
    ("branches", "Latest Builds by Branch"),
)


def validate_yaml_field(value):
    try:
        yaml.safe_load(value)
    except yaml.YAMLError as err:
        raise ValidationError("Error parsing additional YAML: {}".format(err))


class PlanQuerySet(models.QuerySet):
    def for_user(self, user, perms=None):
        if user.is_superuser:
            return self
        if perms is None:
            perms = "plan.view_builds"
        return self.filter(
            planrepository__in=PlanRepository.objects.for_user(user, perms)
        ).distinct()

    def get_for_user_or_404(self, user, query, perms=None):
        try:
            return self.for_user(user, perms).get(**query)
        except Plan.DoesNotExist:
            raise Http404


class Plan(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)
    repos = models.ManyToManyField(
        Repository,
        related_name="plans",
        through="PlanRepository",
        through_fields=("plan", "repo"),
    )
    trigger = models.CharField(max_length=8, choices=TRIGGER_TYPES)
    role = models.CharField(max_length=16, choices=BUILD_ROLES)
    regex = models.CharField(max_length=255, null=True, blank=True)
    flows = models.CharField(max_length=255)
    org = models.CharField(max_length=255)
    context = models.CharField(max_length=255, null=True, blank=True)
    active = models.BooleanField(default=True)
    dashboard = models.CharField(
        max_length=8, choices=DASHBOARD_CHOICES, default=None, null=True, blank=True
    )
    junit_path = models.CharField(max_length=255, null=True, blank=True)
    sfdx_config = models.TextField(null=True, blank=True)
    yaml_config = models.TextField(
        null=True, blank=True, validators=[validate_yaml_field]
    )

    objects = PlanQuerySet.as_manager()

    class Meta:
        ordering = ["name", "active", "context"]

    def get_absolute_url(self):
        return reverse("plan_detail", kwargs={"plan_id": self.id})

    def __str__(self):
        return self.name

    def get_repos(self):
        for repo in self.repos.all():
            yield repo

    def check_push(self, push):
        run_build = False
        commit = None
        commit_message = None

        # Handle commit events
        if self.trigger == "commit":
            # Check if the event was triggered by a commit
            if not push["ref"].startswith("refs/heads/"):
                return run_build, commit, commit_message
            branch = push["ref"][11:]

            # Check the branch against regex
            if not re.match(self.regex, branch):
                return run_build, commit, commit_message

            run_build = True
            commit = push["after"]
            if commit == "0000000000000000000000000000000000000000":
                run_build = False
                commit = None
                return run_build, commit, commit_message

            for commit_info in push.get("commits", []):
                if commit_info["id"] == commit:
                    commit_message = commit_info["message"]
                    break

            # Skip build if commit message contains [ci skip]
            if commit_message and "[ci skip]" in commit_message:
                run_build = False
                commit = None
            return run_build, commit, commit_message

        # Handle tag events
        elif self.trigger == "tag":
            # Check if the event was triggered by a tag
            if not push["ref"].startswith("refs/tags/"):
                return run_build, commit, commit_message
            tag = push["ref"][10:]

            # Check the tag against regex
            if not re.match(self.regex, tag):
                return run_build, commit, commit_message

            run_build = True
            commit = push["head_commit"]["id"]
            return run_build, commit, commit_message

        return run_build, commit, commit_message


class PlanRepositoryQuerySet(models.QuerySet):
    def for_user(self, user, perms=None):
        if user.is_superuser:
            return self
        if not perms:
            perms = "plan.view_builds"
        return get_objects_for_user(user, perms, PlanRepository)

    def get_for_user_or_404(self, user, query, perms=None):
        try:
            return self.for_user(user, perms).get(**query)
        except PlanRepository.DoesNotExist:
            raise Http404

    def should_run(self):
        return self.filter(active=True, plan__active=True)


class PlanRepository(models.Model):
    plan = models.ForeignKey(Plan, on_delete=models.CASCADE)
    repo = models.ForeignKey(Repository, on_delete=models.CASCADE)
    active = models.BooleanField(default=True)

    objects = PlanRepositoryQuerySet.as_manager()

    class Meta:
        ordering = ["repo", "plan"]
        verbose_name_plural = "Plan Repositories"
        base_manager_name = "objects"
        unique_together = ("plan", "repo")
        permissions = (
            ("run_plan", "Run Plan"),
            ("view_builds", "View Builds"),
            ("rebuild_builds", "Rebuild Builds"),
            ("qa_builds", "QA Builds"),
            ("org_login", "Login to Org"),
        )

    def __str__(self):
        return "[{}] {}".format(self.repo, self.plan)

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
    def should_run(self):
        return self.active and self.plan.active


class PlanRepositoryTriggerQuerySet(models.QuerySet):
    def should_run(self):
        return self.filter(active=True, plan__active=True)


class PlanRepositoryTrigger(models.Model):
    plan_repo = models.ForeignKey(PlanRepository, on_delete=models.CASCADE)
    repo = models.ForeignKey(Repository, on_delete=models.CASCADE)
    branch = models.CharField(max_length=255)
    regex = models.CharField(max_length=255, null=True, blank=True)
    trigger = models.CharField(max_length=8, choices=TRIGGER_TYPES)
    active = models.BooleanField(default=True)

    objects = PlanRepositoryTriggerQuerySet.as_manager()

    def fire(self, finished_build):
        repo_id = self.plan_repo.repo.id
        build = Build(
            repo=repo_id,
            plan=self.plan_repo.plan.id,
            planrepo=self.plan_repo.id,
            commit=commit,  # TODO Get this from somewhere?
            commit_message=commit_message,  # TODO Get this from somewhere?
            branch=Branch.object.get(repo=repo_id, name=self.branch),
            build_type="auto",
        )
