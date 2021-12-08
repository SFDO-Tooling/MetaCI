from django.db.models.signals import post_save
from metaci.cumulusci.tasks import fill_pool
from metaci.cumulusci.models import OrgPool

def fill_new_pool(sender, instance, **kwargs):
    fill_pool(instance, instance.minimum_org_count)

post_save.connect(fill_new_pool, sender=OrgPool)