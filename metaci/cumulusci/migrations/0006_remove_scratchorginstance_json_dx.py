# -*- coding: utf-8 -*-
# Generated by Django 1.11.10 on 2018-03-14 17:27
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('cumulusci', '0005_scratchorginstance_delete_error'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='scratchorginstance',
            name='json_dx',
        ),
    ]
