# -*- coding: utf-8 -*-
# Generated by Django 1.10.3 on 2017-02-08 13:44
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("build", "0004_build_keep_org"),
    ]

    operations = [
        migrations.AddField(
            model_name="build",
            name="error_message",
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="build",
            name="exception",
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="buildflow",
            name="error_message",
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="buildflow",
            name="exception",
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name="build",
            name="status",
            field=models.CharField(
                choices=[
                    ("queued", "Queued"),
                    ("waiting", "Waiting"),
                    ("running", "Running"),
                    ("success", "Success"),
                    ("error", "Error"),
                    ("fail", "Failed"),
                ],
                default="queued",
                max_length=16,
            ),
        ),
        migrations.AlterField(
            model_name="rebuild",
            name="status",
            field=models.CharField(
                choices=[
                    ("queued", "Queued"),
                    ("waiting", "Waiting"),
                    ("running", "Running"),
                    ("success", "Success"),
                    ("error", "Error"),
                    ("fail", "Failed"),
                ],
                max_length=16,
            ),
        ),
    ]
