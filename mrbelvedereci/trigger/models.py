from __future__ import unicode_literals

from django.db import models

TRIGGER_TYPES = (
    ('manual', 'Manual'),
    ('commit', 'Commit'),
    ('tag', 'Tag'),
    ('pr', 'Pull Request'),
)

class Trigger(models.Model):
    name = models.CharField(max_length=255)
    type = models.CharField(max_length=8, choices=TRIGGER_TYPES)
    regex = models.CharField(max_length=255, null=True, blank=True)
    build_pr_commits = models.BooleanField(default=False)
    flows = models.CharField(max_length=255)
    org = models.CharField(max_length=255)
    context = models.CharField(max_length=255)
