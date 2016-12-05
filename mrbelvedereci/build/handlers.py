from django.db.models.signals import post_save
from django.dispatch import receiver
from mrbelvedereci.build.models import Build
from mrbelvedereci.build.tasks import run_build

@receiver(post_save, sender=Build)
def queue_build(sender, **kwargs):
    build = kwargs['instance']
    created = kwargs['created']
    if not created:
        return

    # Queue the background job with a 1 second delay to allow the transaction to commit
    run_build.apply_async((build.id,), countdown=1)
