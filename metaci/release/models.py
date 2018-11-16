# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import re

from django.db import models
from django.utils.dateparse import parse_date
from django.utils.dateparse import parse_datetime
from django.utils.translation import ugettext_lazy as _

from model_utils import Choices
from model_utils.models import StatusModel
from model_utils.fields import AutoCreatedField, AutoLastModifiedField

from metaci.release.utils import update_release_from_github
from metaci.repository.utils import get_github_api

class Release(StatusModel):
    STATUS = Choices('draft', 'published', 'hidden')
    created = AutoCreatedField(_('created'))
    modified = AutoLastModifiedField(_('modified'))

    repo = models.ForeignKey('repository.Repository', 
                            on_delete=models.CASCADE, related_name="releases")
    
    version_name = models.CharField(_('version name'), max_length=255, null=True, blank=True)
    version_number = models.CharField(_('version number'), max_length=255, null=True, blank=True)
    package_version_id = models.CharField(_('package version id'), max_length=18, null=True, blank=True)
    git_tag = models.CharField(_('git tag'), max_length=1024, null=True, blank=True)
    github_release = models.URLField(_('github release'), max_length=1024, null=True, blank=True)
    trialforce_id = models.CharField(_('trialforce template id'), max_length=18, null=True, blank=True)

    release_creation_date = models.DateField(_('release creation date'), null=True, blank=True)
    sandbox_push_date = models.DateField(_('sandbox push date'), null=True, blank=True)
    production_push_date = models.DateField(_('production push date'), null=True, blank=True)
    created_from_commit = models.CharField(_('created from commit'), max_length=1024, null=True, blank=True)
    work_item_link = models.URLField(_('work item link'), max_length=1024, null=True, blank=True)

    class Meta:
        get_latest_by = "production_push_date"
        ordering = ['-production_push_date']
        verbose_name = _('release')
        verbose_name_plural = _('releases')
        unique_together = ('repo', 'git_tag')

    def __unicode__(self):
        return "{}: {}".format(self.repo, self.version_name)

    def update_from_github(self):
        update_release_from_github(self)
