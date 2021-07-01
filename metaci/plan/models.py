import re

import yaml
from django.apps import apps
from django.core.exceptions import ValidationError
from django.db import models
from django.http import Http404
from django.urls import reverse
from guardian.shortcuts import get_objects_for_user

from metaci.build.models import Build
from metaci.repository.models import Branch, Repository

TRIGGER_TYPES = (
    ("manual", "Manual"),
    ("commit", "Commit"),
    ("status", "Commit Status"),
    ("tag", "Tag"),
)

BUILD_ROLES = (
    ("beta_release", "Beta Release"),
    ("beta_test", "Beta Test"),
    ("deploy", "Deployment"),
    ("feature", "Feature Test"),
    ("feature_robot", "Feature Test Robot"),
    ("other", "Other"),
    ("push_sandbox", "Push Sandbox"),
    ("push_production", "Push Production"),
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

QUEUES = (
    ("default", "default"),
    ("medium", "medium priority"),
    ("high", "high priority"),
    ("robot", "robot tests"),
    ("long-running", "long-running"),
)


def validate_yaml_field(value):
    try:
        yaml.safe_load(value)
    except yaml.YAMLError as err:
        raise ValidationError(f"Error parsing additional YAML: {err}")


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
    queue = models.CharField(max_length=16, choices=QUEUES, default="default")
    regex = models.CharField(max_length=255, null=True, blank=True)
    flows = models.CharField(max_length=255)
    org = models.CharField(max_length=255)
    context = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        help_text="If set, builds of this plan will update the commit status in GitHub using this context.",
    )
    commit_status_template = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        help_text="Template for the commit message set after a successful build.",
    )
    change_traffic_control = models.BooleanField(
        default=False,
        help_text="Default is set to False, set to true to toggle change traffic control integration on this plan.",
    )
    active = models.BooleanField(default=True)
    keep_org_on_error = models.BooleanField(default=False)
    keep_org_on_fail = models.BooleanField(default=False)
    dashboard = models.CharField(
        max_length=8, choices=DASHBOARD_CHOICES, default=None, null=True, blank=True
    )
    junit_path = models.CharField(max_length=255, null=True, blank=True)
    sfdx_config = models.TextField(null=True, blank=True)
    yaml_config = models.TextField(
        null=True, blank=True, validators=[validate_yaml_field]
    )
    build_timeout = models.IntegerField(default=8 * 60 * 60)

    objects = PlanQuerySet.as_manager()

    class Meta:
        ordering = ["name", "active", "context"]

    def clean(self):
        if self.trigger != "manual" and not self.regex:
            raise ValidationError(
                "Plans with a non-manual trigger type must also specify a regex."
            )

    def get_absolute_url(self):
        return reverse("plan_detail", kwargs={"plan_id": self.id})

    def __str__(self):
        return self.name

    def get_repos(self):
        for repo in self.repos.all():
            yield repo

    def check_github_event(self, event, payload):
        run_build = False
        commit = None
        commit_message = None

        if event == "push":
            # Handle commit events
            if self.trigger == "commit":
                # Check if the event was triggered by a commit
                if not payload["ref"].startswith("refs/heads/"):
                    return run_build, commit, commit_message
                branch = payload["ref"][11:]

                # Check the branch against regex
                if not re.match(self.regex, branch):
                    return run_build, commit, commit_message

                run_build = True
                commit = payload["after"]
                if commit == "0000000000000000000000000000000000000000":
                    run_build = False
                    commit = None
                    return run_build, commit, commit_message

                for commit_info in payload.get("commits", []):
                    if commit_info["id"] == commit:
                        commit_message = commit_info["message"]
                        break

                # Skip build if commit message contains [ci skip]
                if commit_message and "[ci skip]" in commit_message:
                    run_build = False
                    commit = None

            # Handle tag events
            elif self.trigger == "tag":
                # Check if the event was triggered by a tag
                if not payload["ref"].startswith("refs/tags/"):
                    return run_build, commit, commit_message
                tag = payload["ref"][10:]

                # Check the tag against regex
                if not re.match(self.regex, tag):
                    return run_build, commit, commit_message

                run_build = True
                commit = payload["head_commit"]["id"]

        elif (
            event == "status"
            and self.trigger == "status"
            and payload["state"] == "success"
        ):
            if not re.match(self.regex, payload["context"]):
                return run_build, commit, commit_message

            run_build = True
            commit = payload["sha"]

        return run_build, commit, commit_message


SCHEDULE_CHOICES = (
    ("daily", "Daily"),
    ("hourly", "Hourly"),
    ("weekly", "Weekly"),
    ("monthly", "Monthly"),
)


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
        return f"[{self.repo}] {self.plan}"

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
        return self.filter(active=True, target_plan_repo__active=True)


class PlanRepositoryTrigger(models.Model):
    source_plan_repo = models.ForeignKey(
        PlanRepository, on_delete=models.CASCADE, related_name="Sources"
    )
    target_plan_repo = models.ForeignKey(
        PlanRepository, on_delete=models.CASCADE, related_name="Triggers"
    )
    branch = models.CharField(max_length=255)
    active = models.BooleanField(default=True)

    objects = PlanRepositoryTriggerQuerySet.as_manager()

    class Meta:
        ordering = ["target_plan_repo", "source_plan_repo"]
        unique_together = ("target_plan_repo", "source_plan_repo", "branch")
        verbose_name_plural = "Plan Repository Triggers"

    def _get_commit(self):
        repo = self.target_plan_repo.repo.get_github_api()
        branch = repo.branch(self.branch)
        commit = branch.commit.sha
        return commit

    def _get_or_create_branch(self):
        branch, _ = Branch.objects.get_or_create(
            repo=self.target_plan_repo.repo, name=self.branch
        )
        return branch

    def fire(self, finished_build):
        build = Build(
            repo=self.target_plan_repo.repo,
            plan=self.target_plan_repo.plan,
            planrepo=self.target_plan_repo,
            commit=self._get_commit(),
            branch=self._get_or_create_branch(),
            build_type="auto",
        )
        build.save()


class PlanSchedule(models.Model):
    plan = models.ForeignKey(Plan, on_delete=models.CASCADE)
    branch = models.ForeignKey("repository.branch", on_delete=models.CASCADE)
    schedule = models.CharField(max_length=16, choices=SCHEDULE_CHOICES)

    class Meta:
        verbose_name_plural = "Plan Schedules"

    def run(self):
        Build = apps.get_model("build", "Build")
        build = Build(
            repo=self.branch.repo,
            plan=self.plan,
            branch=self.branch,
            commit=self.branch.get_github_api().commit.sha,
            schedule=self,
            build_type="scheduled",
        )
        build.save()
        return build
