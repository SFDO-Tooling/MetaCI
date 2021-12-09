from django.dispatch import receiver

from metaci.build.signals import build_complete
from metaci.cumulusci.tasks import fill_pool, org_claimed


@receiver(build_complete)
def associate_org_instance_to_pool(sender, **kwargs):
    association_helper(sender, **kwargs)


def association_helper(sender, **kwargs):
    build = kwargs.get("build")
    status = kwargs.get("status")

    if status == "success":  # todo Use choices
        build.org_instance.org_pool = build.org_pool
        build.org_instance.save()
    else:
        print("Build did not succeed.")


@receiver(org_claimed)
def backfill_org_pool(sender, **kwargs):
    org_pool = kwargs.get("org_pool")
    fill_pool(org_pool, 1)
