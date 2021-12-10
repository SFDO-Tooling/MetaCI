from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver

from metaci.build.models import Build, Rebuild
from metaci.build.tasks import check_queued_build, set_github_status
from metaci.cumulusci.models import PooledFullBuildOrgRequest, get_org_pool
from metaci.cumulusci.signals import org_claimed


@receiver(post_save, sender=Build)
def queue_build(sender, **kwargs):
    build = kwargs["instance"]
    created = kwargs["created"]
    for_org_pool = bool(build.org_pool)
    print("QUEUE BUILD", build, "Build for pool", for_org_pool)
    if for_org_pool:
        print("Building for full org pool")
    else:
        build_request = PooledFullBuildOrgRequest(
            repo_url=build.planrepo.repo.url,
            plan_name=build.plan.name,
            commit=build.commit,
        )
        org_pool = get_org_pool(build_request)
        if org_pool and org_pool.pooled_orgs.count() > 0:
            print("From org_pool")
            returned_org = org_pool.pooled_orgs.first()
            returned_org.org_pool = None
            returned_org.save()

            build.org = returned_org
            org_claimed.send(sender=org_pool.__class__, org_pool=org_pool)
        else:
            print("Not from org_pool")

    if not created or build.build_type == "manual-command":
        return

    # Queue the pending status task
    if settings.GITHUB_STATUS_UPDATES_ENABLED:
        res_status = set_github_status.delay(build.id)
        build.task_id_status_start = res_status.id

    # Queue the check build task
    res_check = check_queued_build.delay(build.id)
    build.task_id_check = res_check.id

    build.save()


@receiver(post_save, sender=Rebuild)
def queue_rebuild(sender, **kwargs):
    rebuild = kwargs["instance"]
    created = kwargs["created"]

    if not created:
        return

    build = rebuild.build

    if rebuild == build.current_rebuild:
        return

    build.current_rebuild = rebuild

    # Queue the pending status task
    if settings.GITHUB_STATUS_UPDATES_ENABLED:
        res_status = set_github_status.delay(build.id)
        build.task_id_status_start = res_status.id

    # Queue the check build task
    res_check = check_queued_build.delay(build.id)
    build.task_id_check = res_check.id

    build.save()
