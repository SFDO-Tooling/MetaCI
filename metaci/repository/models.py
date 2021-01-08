import github3.exceptions
from cumulusci.core.github import get_github_api_for_repo
from django.apps import apps
from django.db import models
from django.http import Http404
from django.urls import reverse
from model_utils.managers import SoftDeletableManager
from model_utils.models import SoftDeletableModel

from metaci.cumulusci.keychain import GitHubSettingsKeychain


class RepositoryQuerySet(models.QuerySet):
    def for_user(self, user, perms=None):
        if user.is_superuser:
            return self
        if perms is None:
            perms = "plan.view_builds"
        PlanRepository = apps.get_model("plan.PlanRepository")
        return self.filter(
            planrepository__in=PlanRepository.objects.for_user(user, perms)
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
        ordering = ["name", "owner"]
        verbose_name_plural = "repositories"

    def get_absolute_url(self):
        return reverse("repo_detail", kwargs={"owner": self.owner, "name": self.name})

    def __str__(self):
        return f"{self.owner}/{self.name}"

    def get_github_api(self):
        gh = get_github_api_for_repo(GitHubSettingsKeychain(), self.owner, self.name)
        repo = gh.repository(self.owner, self.name)
        return repo

    @property
    def latest_release(self):
        try:
            return self.releases.latest()
        except Repository.DoesNotExist:
            return None


class BranchManager(SoftDeletableManager):
    def get_queryset(self):
        return super().get_queryset().select_related("repo")


class Branch(SoftDeletableModel):
    name = models.CharField(max_length=255)
    repo = models.ForeignKey(
        Repository, related_name="branches", on_delete=models.CASCADE
    )
    objects = BranchManager()
    include_deleted = models.QuerySet.as_manager()

    class Meta:
        ordering = ["repo__name", "repo__owner", "name"]
        verbose_name_plural = "branches"

    def get_absolute_url(self):
        return reverse(
            "branch_detail",
            kwargs={
                "owner": self.repo.owner,
                "name": self.repo.name,
                "branch": self.name,
            },
        )

    def __str__(self):
        return f"{self.repo.name}: {self.name}"

    def is_tag(self):
        """Returns True if this branch is related to a tag in GitHub"""
        return self.name.startswith("tag: ")

    def get_github_api(self):
        try:
            branch = self.repo.get_github_api().branch(self.name)
        except github3.exceptions.NotFoundError:
            branch = None
        return branch
