# -*- coding: utf-8 -*-
# Generated by Django 1.10.7 on 2017-11-18 00:34
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('cumulusci', '0007_org_orgmartdata'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='org',
            name='scratch',
        ),
    ]
