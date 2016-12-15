from celery import shared_task
from django.core.cache import cache
from mrbelvedereci.salesforce.models import Org
from mrbelvedereci.github.utils import create_status

@shared_task
def run_build(build_id, lock_id=None):
    from mrbelvedereci.build.models import Build
    try:
        build = Build.objects.get(id=build_id)
        exception = None
        build.run()
        set_github_status.apply_async((build_id,), countdown=1)
    
    except:
        if lock_id:
            cache.delete(lock_id)
        set_github_status.apply_async((build_id,), countdown=1)
        
        raise

    if lock_id:
        cache.delete(lock_id)

    return build.status

@shared_task(bind=True)
def check_queued_build(self, build_id):
    from mrbelvedereci.build.models import Build
    build = Build.objects.get(id = build_id)

    # Check for concurrency blocking
    try:
        org = Org.objects.get(name = build.trigger.org, repo = build.repo)
    except Org.DoesNotExist:
        return

    if org.scratch:
        # For scratch orgs, we don't need concurrency blocking logic, just run the build
        run_build.apply_async((build.id,), countdown=1)
    
    else:
        # For persistent orgs, use the cache to lock the org
        lock_id = 'mrbelvedereci-org-lock-{}'.format(org.id)
        status = cache.add(lock_id, 'build-{}'.format(build_id))
        
        if status is True:
            # Lock successful, run the build
            run_build.apply_async((build.id,lock_id), countdown=1)
        else:
            # Failed to get lock, queue next check in 5 seconds
            check_queued_build.apply_async((build.id,), countdown=5)

@shared_task
def set_github_status(build_id):
    from mrbelvedereci.build.models import Build
    build = Build.objects.get(id = build_id)
    create_status(build)
