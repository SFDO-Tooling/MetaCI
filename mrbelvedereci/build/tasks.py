import django_rq
import time
from django.core.cache import cache
from mrbelvedereci.cumulusci.models import Org
from mrbelvedereci.repository.utils import create_status
from mrbelvedereci.build.signals import build_complete

@django_rq.job('default', timeout=28800)
def run_build(build_id, lock_id=None):
    from mrbelvedereci.build.models import Build
    try:
        build = Build.objects.get(id=build_id)
        exception = None
        build.run()
        res_status = set_github_status.delay(build_id)
        build.task_id_status_end = res_status.id
        build.save()

        build_complete.send(sender=build.__class__, build=build, status=build.status)
    
    except Exception as e:
        if lock_id:
            cache.delete(lock_id)

        res_status = set_github_status.delay(build_id)
        build.task_id_status_end = res_status.id
        build.status = 'error'
        build.log += '\nERROR: The build raised an exception\n'
        build.log += unicode(e)
        build.save()

        build_complete.send(sender=build.__class__, build=build, status=build.status)

    if lock_id:
        cache.delete(lock_id)

    return build.status

@django_rq.job('short', timeout=60)
def check_queued_build(build_id):
    from mrbelvedereci.build.models import Build
    try:
        build = Build.objects.get(id = build_id)
    except Build.DoesNotExist:
        time.sleep(1)
        check_queued_build.delay(build_id)

    # Check for concurrency blocking
    try:
        org = Org.objects.get(name = build.plan.org, repo = build.repo)
    except Org.DoesNotExist:
        return

    if org.scratch:
        # For scratch orgs, we don't need concurrency blocking logic, just run the build
        res_run = run_build.delay(build.id)
        build.task_id_run = res_run.id
    
    else:
        # For persistent orgs, use the cache to lock the org
        lock_id = 'mrbelvedereci-org-lock-{}'.format(org.id)
        status = cache.add(lock_id, 'build-{}'.format(build_id))
        
        if status is True:
            # Lock successful, run the build
            res_run = run_build.delay(build.id, lock_id)
            build.task_id_run = res_run.id
            build.save()
        else:
            # Failed to get lock, queue next check
            time.sleep(1)
            res_check = check_queued_build.delay(build.id)
            build.task_id_check = res_check.id
            build.save()

@django_rq.job('short')
def set_github_status(build_id):
    from mrbelvedereci.build.models import Build
    build = Build.objects.get(id = build_id)
    create_status(build)

@django_rq.job('short')
def check_build_tasks():
    from mrbelvedereci.build.models import Build
    builds = Build.objects.filter(status = 'running')
    for build in builds:
        task_id = build.task_id_run
