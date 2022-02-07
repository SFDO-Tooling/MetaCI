import datetime
from typing import Optional

from django.core.exceptions import ValidationError
from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from model_utils import Choices
from model_utils.fields import AutoCreatedField, AutoLastModifiedField
from model_utils.models import StatusModel
from pydantic import BaseModel

from metaci.plan.models import PlanRepository
from metaci.release.utils import update_release_from_github


class ReleaseCohort(models.Model):
    name = models.CharField(_("name"), max_length=255)
    STATUS = Choices(
        ("planned", _("Planned")),
        ("approved", _("Approved")),
        ("active", _("Active")),
        ("canceled", _("Canceled")),
        ("completed", _("Completed")),
        ("failed", _("Failed")),
    )
    status = models.CharField(
        max_length=9,
        choices=STATUS,
        default=STATUS.planned,
    )
    merge_freeze_start = models.DateTimeField(_("Merge Freeze Start Time"))
    merge_freeze_end = models.DateTimeField(_("Merge Freeze End Time"))
    error_message = models.TextField(null=True, blank=True)
    dependency_graph = models.JSONField(null=True, blank=True)

    # Fields for MetaPush integration
    metapush_push_schedule_id = models.CharField(max_length=32, null=True, blank=True)
    enable_metapush = models.BooleanField(default=True)
    metapush_error = models.TextField(null=True, blank=True)
    metapush_push_cohort_id = models.CharField(max_length=32, null=True, blank=True)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("cohort_detail", kwargs={"cohort_id": str(self.id)})

    def clean(self):
        now = datetime.datetime.now(tz=datetime.timezone.utc)
        if (self.merge_freeze_start <= now and self.merge_freeze_end >= now) ^ (
            self.status == ReleaseCohort.STATUS.active
        ):
            raise ValidationError(
                _(
                    "A Release Cohort must be in Active status during its merge freeze date range."
                )
            )

        if (self.merge_freeze_end <= now) and self.status not in [
            ReleaseCohort.STATUS.completed,
            ReleaseCohort.STATUS.canceled,
            ReleaseCohort.STATUS.failed,
        ]:
            raise ValidationError(
                _(
                    "A Release Cohort must be in a completion status after its merge freeze date range."
                )
            )

        if (
            self.merge_freeze_end > now
            and self.status == ReleaseCohort.STATUS.completed
        ):
            raise ValidationError(
                _(
                    "A Release Cohort may not be in Completed status until after its merge freeze date range."
                )
            )


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
    push_time = models.DateTimeField(_("push_time"), null=True, blank=True)
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
    push_time: Optional[int] = None
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

    def _push_time(self, start):
        if self.push_time is None:
            return None
        return timezone.make_aware(
            datetime.datetime.combine(start.date(), datetime.time(self.push_time))
        )


class Release(StatusModel):
    STATUS = Choices(
        ("draft", _("Draft")),
        ("failed", _("Failed")),
        ("completed", _("Completed")),
        ("inprogress", _("In Progress")),
        ("waiting", _("Waiting")),
        ("blocked", _("Blocked")),
    )
    FAILED_STATUSES = [STATUS.failed]
    COMPLETED_STATUSES = [STATUS.completed, *FAILED_STATUSES]
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
    error_message = models.TextField(_("error message"), null=True, blank=True)

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
        _("created from commit"), max_length=1024, null=True, blank=False
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
    release_cohort = models.ForeignKey(
        "release.ReleaseCohort",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        default=None,
        related_name="releases",
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
        # We don't allow adding a Release to a Release Cohort other than in Planned status.
        # We also don't allow reparenting from one Release Cohort to another unless both Cohorts
        # are in Planned status.
        if not self.pk:
            old_cohort = None
        else:
            old_cohort = Release.objects.get(pk=self.pk).release_cohort

        if old_cohort != self.release_cohort:
            if (
                self.release_cohort
                and self.release_cohort.status != ReleaseCohort.STATUS.planned
            ):
                raise ValidationError(
                    _("Releases must be added to a Release Cohort in Planned status.")
                )

            if old_cohort and old_cohort.status != ReleaseCohort.STATUS.planned:
                raise ValidationError(
                    _(
                        "Releases cannot be removed from a Release Cohort that is not in Planned status."
                    )
                )

        super().save(*args, **kw)
        for step_dict in self.repo.default_implementation_steps:
            if len(step_dict) > 0:
                step = DefaultImplementationStep(**step_dict)
                self.create_default_implementation_step(step)

    def create_default_implementation_step(self, step: DefaultImplementationStep):
        """Create default implementation steps"""
        if len(self.implementation_steps.filter(plan__role=f"{step.role}")) < 1:
            try:
                planrepo = self.repo.planrepos.should_run().get(
                    plan__role=f"{step.role}"
                )
            except (
                PlanRepository.DoesNotExist,
                PlanRepository.MultipleObjectsReturned,
            ):
                pass
            else:
                start = step.start(self)
                push = step._push_time(start)
                ImplementationStep(
                    release=self,
                    plan=planrepo.plan,
                    push_time=push,
                    start_time=start,
                    stop_time=step.end(start),
                ).save()
