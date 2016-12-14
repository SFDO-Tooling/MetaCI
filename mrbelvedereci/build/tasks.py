from celery import shared_task
from mrbelvedereci.build.models import Build
from mrbelvedereci.salesforce.models import Org

@shared_task
def run_build(build_id):
    build = Build.objects.get(id=build_id)
    build.run()
    return build.status

@shared_task
def check_queued_build(build_id):
    build = Build.objects.get(id = build_id)

    # Check for concurrency blocking
    try:
        org = Org.objects.get(name = build.trigger.org, repo = build.repo)
    except Org.DoesNotExist:
        return

    # If this is not a scratch org, ensure no builds are currently running against the org
    if not org.scratch:
        running_builds = Build.objects.filter(status='running', repo=build.repo, org = build.org).count()
        if running_builds:
            # Requeue this job to check again in 5 seconds
            check_queued_build.apply_async((build.id,), countdown=5)
            return 'Queued: checking again in 5 seconds'

    # Queue the background job with a 1 second delay to allow the transaction to commit
    run_build.apply_async((build.id,), countdown=1)
