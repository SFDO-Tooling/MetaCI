from __future__ import unicode_literals

from django.db import models

class Org(models.Model):
    name = models.CharField(max_length=255)
    json = models.TextField()
    scratch = models.BooleanField(default=False)
    repo = models.ForeignKey('github.Repository', related_name='orgs')

    def __unicode__(self):
        return '{}: {}'.format(self.repo.name, self.name)
