from __future__ import unicode_literals

from django.db import models

class OrgConfig(models.Model):
    name = models.CharField(max_length=255)
    json = models.TextField()
    scratch = models.BooleanField(default=False)
