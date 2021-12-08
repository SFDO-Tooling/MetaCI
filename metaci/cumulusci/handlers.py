from django.dispatch import receiver

from metaci.build.signals import build_complete
from metaci.build.models import BUILD_STATUSES


@receiver(build_complete)
def associate_org_instance_to_pool(sender, **kwargs):
    build = kwargs.get("build")

    if build.status == BUILD_STATUSES.success:
        build.org_instance.org_pool = build.org_pool
        build.org_instance.save()
