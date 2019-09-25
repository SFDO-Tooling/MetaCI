from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver

from metaci.build.models import Build
from metaci.build.models import Rebuild
from metaci.build.tasks import check_waiting_builds
from metaci.build.tasks import set_github_status


@receiver(post_save, sender=Build)
def queue_build(sender, **kwargs):
    build = kwargs["instance"]
    created = kwargs["created"]
    if not created:
        return

    # Queue the pending status task
    if settings.GITHUB_STATUS_UPDATES_ENABLED:
        res_status = set_github_status.delay(build.id)
        build.task_id_status_start = res_status.id

    # Queue the check build task
    build.save()
    check_waiting_builds.delay()


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
    build.save()
    check_waiting_builds.delay()
