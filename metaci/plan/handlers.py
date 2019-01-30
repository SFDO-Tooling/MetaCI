from django.dispatch import receiver
from metaci.build.signals import build_complete
from metaci.plan.models import PlanRepositoryTrigger


@receiver(build_complete)
def trigger_dependent_builds(sender, **kwargs):
    build = kwargs.get("build")
    status = kwargs.get("status")
    if status is not "success":
        return
    triggers = PlanRepositoryTrigger.objects.should_run().filter(repo=build.repo)
    for trigger in triggers:
        trigger.fire(build)
