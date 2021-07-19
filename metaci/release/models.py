import datetime

from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from model_utils import Choices
from model_utils.fields import AutoCreatedField, AutoLastModifiedField
from model_utils.models import StatusModel
from pydantic import BaseModel

from metaci.plan.models import PlanRepository
from metaci.release.utils import update_release_from_github


class ChangeCaseTemplate(models.Model):
    name = models.CharField(_("name"), max_length=255)
    case_template_id = models.CharField(_("case template id"), max_length=18)

    def __str__(self):
        return self.name


class ImplementationStep(models.Model):
    release = models.ForeignKey(
        "release.Release", on_delete=models.CASCADE, related_name="implementation_steps"
    )
    plan = models.ForeignKey(
        "plan.Plan", on_delete=models.CASCADE, related_name="implementation_steps"
    )
    start_time = models.DateTimeField(_("start_time"))
    stop_time = models.DateTimeField(_("stop_time"))
    external_id = models.CharField(
        _("external id"), max_length=255, null=True, blank=True
    )

    class Meta:
        ordering = ("start_time",)
        unique_together = ("release", "plan")

    def __str__(self):
        return self.plan.name


def get_default_sandbox_date():
    return datetime.date.today()


def get_default_production_date():
    return datetime.date.today() + datetime.timedelta(days=6)


class DefaultImplementationStep(BaseModel):
    start_date_offset: int = 0
    start_time: int
    duration: int
    role: str

    def start(self, release):
        return timezone.make_aware(
            datetime.datetime.combine(
                release.release_creation_date
                + datetime.timedelta(days=self.start_date_offset),
                datetime.time(self.start_time),
            )
        )

    def end(self, start):
        return start + datetime.timedelta(hours=self.duration)


class Release(StatusModel):
    STATUS = Choices("draft", "published", "hidden")
    created = AutoCreatedField(_("created"))
    modified = AutoLastModifiedField(_("modified"))

    repo = models.ForeignKey(
        "repository.Repository", on_delete=models.CASCADE, related_name="releases"
    )

    version_name = models.CharField(
        _("version name"), max_length=255, null=True, blank=True
    )
    version_number = models.CharField(
        _("version number"), max_length=255, null=False, blank=False
    )
    package_version_id = models.CharField(
        _("package version id"), max_length=18, null=True, blank=True
    )
    git_tag = models.CharField(_("git tag"), max_length=1024, null=True)
    github_release = models.URLField(
        _("github release"), max_length=1024, null=True, blank=True
    )
    trialforce_id = models.CharField(
        _("trialforce template id"), max_length=18, null=True, blank=True
    )

    release_creation_date = models.DateField(
        _("release creation date"),
        null=True,
        blank=True,
        default=get_default_sandbox_date,
    )
    sandbox_push_date = models.DateField(
        _("sandbox push date"),
        null=True,
        blank=True,
        default=get_default_sandbox_date,
    )
    production_push_date = models.DateField(
        _("production push date"),
        null=True,
        blank=True,
        default=get_default_production_date,
    )
    created_from_commit = models.CharField(
        _("created from commit"), max_length=1024, null=True, blank=True
    )
    work_item_link = models.URLField(
        _("work item link"), max_length=1024, null=True, blank=True
    )
    change_case_template = models.ForeignKey(
        "release.ChangeCaseTemplate",
        on_delete=models.PROTECT,
        null=False,
        blank=False,
    )
    change_case_link = models.CharField(
        _("change case ID"), max_length=1024, null=True, blank=True
    )

    class Meta:
        get_latest_by = "created"
        ordering = ["-created"]
        verbose_name = _("release")
        verbose_name_plural = _("releases")
        unique_together = ("repo", "git_tag")

    def __str__(self):
        return f"{self.repo}: {self.version_name}"

    def update_from_github(self):
        update_release_from_github(self)

    def save(self, *args, **kw):
        super().save(*args, **kw)
        for step_dict in self.repo.default_implementation_steps:
            if len(step_dict) > 0:
                step = DefaultImplementationStep(**step_dict)
                self.create_default_implementation_step(step)

    def create_default_implementation_step(self, step: DefaultImplementationStep):
        """Create default implementation steps"""
        if len(self.implementation_steps.filter(plan__role=f"{step.role}")) < 1:
            try:
                planrepo = self.repo.planrepository_set.should_run().get(
                    plan__role=f"{step.role}"
                )
            except (
                PlanRepository.DoesNotExist,
                PlanRepository.MultipleObjectsReturned,
            ):
                pass
            else:
                start = step.start(self)
                ImplementationStep(
                    release=self,
                    plan=planrepo.plan,
                    start_time=start,
                    stop_time=step.end(start),
                ).save()
