from django.dispatch import receiver

from metaci.build.signals import build_complete
from metaci.plan.models import PlanRepositoryTrigger


@receiver(build_complete)
def trigger_dependent_builds(sender, **kwargs):
    build = kwargs.get("build")
    status = kwargs.get("status")
    if status != "success":
        return
    triggers = PlanRepositoryTrigger.objects.should_run().filter(
        source_plan_repo=build.planrepo
    )
    for trigger in triggers:
        try:
            trigger.fire(build)
        except Exception as e:
            build.log += (
                f"Could not trigger plan {trigger.target_plan_repo} ({trigger.branch} branch): "
                f"{e.__class__.__name__} {str(e)}"
            )
            build.save()
            # Intentionally swallow the exception,
            # so that we don't error the trigger build or block other triggers.
