from django import dispatch
from django.db.models.signals import post_save

from metaci.cumulusci.models import OrgPool
from metaci.cumulusci.tasks import fill_pool

# Sent whenever an org is claimed from an org pool
# provided signal args: 'org_pool'
org_claimed = dispatch.Signal()


def fill_new_pool(sender, instance, **kwargs):
    fill_pool(instance, instance.minimum_org_count)


post_save.connect(fill_new_pool, sender=OrgPool)
