from __future__ import unicode_literals

from django.db import models

class Repository(models.Model):
    name = models.CharField(max_length=255)
    owner = models.CharField(max_length=255)
    github_id = models.IntegerField(null=True, blank=True)
    url = models.URLField(max_length=255)

    def __unicode__(self):
        return '{}/{}'.format(self.owner, self.name)
    
class Branch(models.Model):
    name = models.CharField(max_length=255)
    repo = models.ForeignKey(Repository, related_name='branches')
    deleted = models.BooleanField(default=False)

    def __unicode__(self):
        return unicode(self.name)
