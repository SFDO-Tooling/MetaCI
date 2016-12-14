from contextlib import contextmanager
from celery import shared_task
from celery.five import monotonic
from django.core.cache import cache
from mrbelvedereci.build.models import Build
from mrbelvedereci.salesforce.models import Org

LOCK_EXPIRE = 60 * 120  # Lock expires in 2 hours

@contextmanager
def lock_org(lock_id, oid):
    timeout_at = monotonic() + LOCK_EXPIRE - 3
    # cache.add fails if the key already exists
    status = cache.add(lock_id, oid, LOCK_EXPIRE)
    try:
        yield status
    finally:
        # memcache delete is very slow, but we have to use it to take
        # advantage of using add() for atomic locking
        if monotonic() < timeout_at:
            # don't release the lock if we exceeded the timeout
            # to lessen the chance of releasing an expired lock
            # owned by someone else.
            cache.delete(lock_id)

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
        lock_id = 'mrbelvedereci-org-lock-{1}'.format(org.id)
        logger.debug('Locking org: %s', org)
        with memcache_lock(lock_id, self.app.oid) as acquired:
            if acquired:
                # Run the build
                run_build.apply_async((build.id,), countdown=1)
            else:
                # Queue next check in 5 seconds
                check_queued_build.apply_async((build.id,), countdown=5)
    # For scratch orgs, don't worry about locking, just run the build
    else:
        run_build.apply_async((build.id,), countdown=1)
