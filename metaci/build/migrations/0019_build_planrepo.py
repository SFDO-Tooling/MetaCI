# -*- coding: utf-8 -*-
# Generated by Django 1.11.10 on 2018-10-18 18:43
from __future__ import unicode_literals

from django.core.exceptions import ObjectDoesNotExist
from django.db import migrations, models
import django.db.models.deletion


def set_planrepository(apps, schema_editor):
    Build = apps.get_model("build", "Build")
    for build in Build.objects.all().iterator():
        try:
            build.planrepo = build.plan.planrepos.get(repo = build.repo)
        except ObjectDoesNotExist:
            continue
        build.save()


class Migration(migrations.Migration):

    dependencies = [
        ("plan", "0020_auto_20181018_1636"),
        ("build", "0018_remove_build_schedule"),
    ]

    operations = [
        migrations.AddField(
            model_name="build",
            name="planrepo",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="builds",
                to="plan.PlanRepository",
            ),
            preserve_default=False,
        ),
        migrations.RunPython(set_planrepository),
    ]
