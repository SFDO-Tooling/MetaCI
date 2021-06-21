from django.contrib.auth.models import Group
from django.db.models.signals import post_save
from django.dispatch import receiver
from guardian.conf import settings as guardian_settings

from metaci.users.models import User


@receiver(post_save, sender=User)
def add_public_group(sender, **kwargs):
    user = kwargs["instance"]
    created = kwargs["created"]
    if not created:
        return

    if user.username == guardian_settings.ANONYMOUS_USER_NAME:
        return

    user.groups.add(Group.objects.get(name="Public"))
