from django import db, dispatch
from django.db.models.signals import post_save
from django.utils import timezone
from django_rq import job

from metaci.build.models import Build
from metaci.cumulusci.models import OrgPool, ScratchOrgInstance
from metaci.plan.models import Plan

# Sent whenever an org is claimed from an org pool
# provided signal args: 'org_pool'
org_claimed = dispatch.Signal()


def fill_new_pool(sender, instance, created, **kwargs):
    if created:
        fill_pool(instance, instance.minimum_org_count)


post_save.connect(fill_new_pool, sender=OrgPool)


@job("short")
def prune_orgs():
    """An RQ task to mark expired orgs as deleted.

    We don't need to bother calling delete_org on each expired scratch
    org, we'll trust that the org expires, and just efficiently flip the
    bits in MetaCI so that they don't show up on list views anymore.
    """
    db.connection.close()
    pruneing_qs = ScratchOrgInstance.expired.all()
    count = pruneing_qs.update(
        deleted=True, time_deleted=timezone.now(), delete_error="Org is expired."
    )
    return f"pruned {count} orgs"


@job("short")
def top_up_org_pools():
    """An RQ task to top up any existing Org Pools
    as needed due to expiry or having been used
    """
    for pool in OrgPool.objects.all():
        good_org_count = 0

        # do you have enough orgs w/ required minimum lifespan remaining to satisfy the pool?
        for org in pool.pooled_orgs.all():
            if org.days > pool.minimum_lifespan:
                good_org_count += 1
        # or do you have builds already running?
        good_org_count += pool.builds.filter(status="running")

        orgs_short = pool.minimum_org_count - good_org_count
        if orgs_short > 0:
            fill_pool(pool, orgs_short)


def fill_pool(pool: OrgPool, count: int):
    plan = Plan.objects.filter(role="pool_org").first()
    for i in range(count):
        build = Build(
            repo=pool.repository,
            plan=plan,
            org_pool=pool,
            # branch="main",
            commit="main",
            keep_org=True,
            build_type="pool",
        )

        build.save()
