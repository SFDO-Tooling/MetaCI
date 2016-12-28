from django.db.models.signals import post_save
from django.dispatch import receiver
from mrbelvedereci.build.models import Build
from mrbelvedereci.build.tasks import check_queued_build
from mrbelvedereci.build.tasks import set_github_status

@receiver(post_save, sender=Build)
def queue_build(sender, **kwargs):
    build = kwargs['instance']
    created = kwargs['created']
    if not created:
        return

    # Queue the pending status task
    res_status = set_github_status.apply_async((build.id,), countdown=1)
    build.task_id_status_start = res_status.task_id

    # Queue the check build task
    res_check = check_queued_build.apply_async((build.id,), countdown=1)
    build.task_id_check = res_check.task_id

    build.save()
