# -*- coding: utf-8 -*-
# Generated by Django 1.10.7 on 2017-11-16 21:17
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('repository', '0002_auto_20171031_2037'),
        ('cumulusci', '0010_auto_20171116_2101'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='org',
            unique_together=set([('repo', 'name')]),
        ),
    ]
