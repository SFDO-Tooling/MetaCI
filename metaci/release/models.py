# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import datetime

from django.db import models
from django.utils.translation import ugettext_lazy as _
from model_utils import Choices
from model_utils.fields import AutoCreatedField, AutoLastModifiedField
from model_utils.models import StatusModel

from metaci.release.utils import update_release_from_github


class ChangeCaseTemplate(models.Model):
    name = models.CharField(_("name"), max_length=255)
    case_template_id = models.CharField(_("case template id"), max_length=18)

    def __str__(self):
        return self.name


class Release(StatusModel):
    def get_sandbox_date():
        return datetime.date.today()

    def get_production_date():
        return datetime.date.today() + datetime.timedelta(days=6)

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
        _("version number"), max_length=255, null=True, blank=True
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
        default=get_sandbox_date,
    )
    sandbox_push_date = models.DateField(
        _("sandbox push date"),
        null=True,
        blank=True,
        default=get_sandbox_date,
    )
    production_push_date = models.DateField(
        _("production push date"),
        null=True,
        blank=True,
        default=get_production_date,
    )
    created_from_commit = models.CharField(
        _("created from commit"), max_length=1024, null=True, blank=True
    )
    work_item_link = models.URLField(
        _("work item link"), max_length=1024, null=True, blank=True
    )
    change_case_template = models.ForeignKey(
        "release.ChangeCaseTemplate", on_delete=models.SET_NULL, null=True
    )
    change_case_link = models.URLField(
        _("change case link"), max_length=1024, null=True, blank=True
    )

    class Meta:
        get_latest_by = "production_push_date"
        ordering = ["-git_tag"]
        verbose_name = _("release")
        verbose_name_plural = _("releases")
        unique_together = ("repo", "git_tag")

    def __str__(self):
        return f"{self.repo}: {self.version_name}"

    def update_from_github(self):
        update_release_from_github(self)
