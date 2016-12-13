from __future__ import unicode_literals
import re

from django.db import models

TRIGGER_TYPES = (
    ('manual', 'Manual'),
    ('commit', 'Commit'),
    ('tag', 'Tag'),
)

class Trigger(models.Model):
    name = models.CharField(max_length=255)
    repo = models.ForeignKey('github.Repository', related_name="triggers")
    type = models.CharField(max_length=8, choices=TRIGGER_TYPES)
    regex = models.CharField(max_length=255, null=True, blank=True)
    flows = models.CharField(max_length=255)
    org = models.CharField(max_length=255)
    context = models.CharField(max_length=255)

    def __unicode__(self):
        return unicode(self.name)

    def check_push(self, push):
        # Handle commit events
        if self.type == 'commit':
            # Check if the event was triggered by a commit
            if not push['ref'].startswith('refs/heads/'):
                return False
            branch = push['ref'][11:]

            # Check the branch against regex
            if not re.match(self.regex, branch):
                return False
            return True

        # Handle tag events
        elif self.type == 'tag':
            # Check if the event was triggered by a tag
            if not push['ref'].startswith('refs/tags/'):
                return False
            tag = push['ref'][10:]
            
            # Check the tag against regex
            if not re.match(self.regex, tag):
                return False
            return True
    
        return False
