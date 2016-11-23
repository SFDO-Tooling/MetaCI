from __future__ import unicode_literals

from django.db import models

BUILD_STATUSES = (
    ('queued', 'Queued'),
    ('running', 'Running'),
    ('success', 'Success'),
    ('error', 'Error'),
    ('fail', 'Failed'),
)

class Build(models.Model):
    repo = models.ForeignKey('github.Repository', related_name='builds')
    branch = models.ForeignKey('github.Branch', related_name='builds', null=True, blank=True)
    commit = models.CharField(max_length=32)
    tag = models.CharField(max_length=255, null=True, blank=True)
    pr = models.IntegerField(null=True, blank=True)
    trigger = models.ForeignKey('trigger.Trigger', related_name='builds')
    log = models.TextField(null=True, blank=True)
    status = models.CharField(max_length=8, choices=BUILD_STATUSES, default='queued')
    time_queue = models.DateTimeField(auto_now_add=True)
    time_start = models.DateTimeField(null=True, blank=True)
    time_end = models.DateTimeField(null=True, blank=True) 

    def __unicode__(self):
        return '{}: {} - {}'.format(self.id, self.repo, self.commit)
