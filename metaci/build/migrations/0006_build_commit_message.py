# -*- coding: utf-8 -*-
# Generated by Django 1.10.3 on 2017-02-08 14:14
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("build", "0005_auto_20170208_1344"),
    ]

    operations = [
        migrations.AddField(
            model_name="build",
            name="commit_message",
            field=models.TextField(blank=True, null=True),
        ),
    ]
