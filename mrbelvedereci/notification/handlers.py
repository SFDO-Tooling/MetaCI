from django.dispatch import receiver
from mrbelvedereci.build.signals import build_complete
from mrbelvedereci.notification.tasks import queue_build_notifications

@receiver(build_complete)
def enqueue_queue_build_notifications(sender, **kwargs):
    build = kwargs.get('build')
    queue_build_notifications.delay(build.id)
