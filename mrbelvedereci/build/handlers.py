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
    set_github_status.apply_async((build, 'pending'), countdown=1)
    check_queued_build.apply_async((build.id,), countdown=1)
