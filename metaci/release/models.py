# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models

# Create your models here.



class ReleasePlanItemDefinition(models.Model):
    # ordering? some django package for that!!!!
    step_num = models.IntegerField()
    repo = models.ForeignKey('repository.Repository')
    plan = models.ForeignKey('plan.Plan', null=True, false=True)
    subject = models.CharField(max_length=500)
    description = models.TextField()
    manual = models.BooleanField()
    overrideable = models.BooleanField()
    # inputs / outputs???

class ReleasePlan(models.Model):
    repo = models.ForeignKey('repository.Repository')
    beta_tag = models.CharField(max_length=500)
    beta_commit = models.CharField(max_length=50)
    all_package_version_id = models.CharField(max_length=18, help='04t ID')
    release_tag = models.CharField(max_length=500)
    # github IDs? URLs?
    # how to represent the push(es)? steps i think since theyre just tasks.

class ReleasePlanItem(models.Model):
    release_plan = models.ForeignKey(ReleasePlan)
    definition = models.ForeignKey(ReleasePlanItemDefinition)
    build = models.ForeignKey('build.Build', null=True, blank=True)
    # inputs / outputs???