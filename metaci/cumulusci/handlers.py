from django.dispatch import receiver

from metaci.build.models import BUILD_STATUSES
from metaci.build.signals import build_complete
from metaci.cumulusci.tasks import org_claimed
from metaci.cumulusci.tasks import fill_pool


@receiver(build_complete)
def associate_org_instance_to_pool(sender, **kwargs):
    build = kwargs.get("build")
    status = kwargs.get("status")

    if status == BUILD_STATUSES.success:
        build.org_instance.org_pool = build.org_pool
        build.org_instance.save()


@receiver(org_claimed)
def backfill_org_pool(sender, **kwargs):
    org_pool = kwargs.get("org_pool")
    fill_pool(org_pool, 1)
