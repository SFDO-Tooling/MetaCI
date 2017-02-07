import django_rq
import os
import requests
import time
from django import db
from django.core.cache import cache
from mrbelvedereci.cumulusci.models import Org
from mrbelvedereci.repository.utils import create_status
from mrbelvedereci.build.signals import build_complete

BUILD_TIMEOUT=28800

def reset_database_connection():
    db.connection.close()

@django_rq.job('default', timeout=BUILD_TIMEOUT)
def run_build(build_id, lock_id=None):
    reset_database_connection()
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

    # Restart the Heroku dyno if on Heroku
    dyno_id = os.environ.get('HEROKU_DYNO_ID')
    api_token = os.environ.get('HEROKU_API_TOKEN')
    app_id = os.environ.get('HEROKU_APP_ID')
    if dyno_id and api_token and app_id:
        headers = {
            'Accept': "application/vnd.heroku+json; version=3",
            "Authorization": "Bearer {}".format(api_token),
        }
        resp = requests.delete('https://api.heroku.com/apps/{}/dynos/{}'.format(app_id, dyno_id), headers=headers)
    
    return build.status

@django_rq.job('short', timeout=60)
def check_queued_build(build_id):
    reset_database_connection()

    from mrbelvedereci.build.models import Build
    build = Build.objects.get(id = build_id)

    if build.status != 'queued':
        return 'Build is not queued.  Current build status is {}'.format(build.status)

    # Check for concurrency blocking
    try:
        org = Org.objects.get(name = build.plan.org, repo = build.repo)
    except Org.DoesNotExist:
        message = 'Could not find org configuration for org {}'.format(build.plan.org)
        build.log = message
        build.status = 'error'
        build.save()
        return 'Could not find org configuration for org {}'.format(build.plan.org)

    if org.scratch:
        # For scratch orgs, we don't need concurrency blocking logic, just run the build
        res_run = run_build.delay(build.id)
        build.task_id_check = None
        build.task_id_run = res_run.id
        build.save()
        return "Org is a scratch org, running build concurrently as task {}".format(res_run.id)
    
    else:
        # For persistent orgs, use the cache to lock the org
        lock_id = 'mrbelvedereci-org-lock-{}'.format(org.id)
        status = cache.add(lock_id, 'build-{}'.format(build_id), timeout=BUILD_TIMEOUT)
        
        if status is True:
            # Lock successful, run the build
            res_run = run_build.delay(build.id, lock_id)
            build.task_id_run = res_run.id
            build.save()
            return "Got a lock on the org, running as task {}".format(res_run.id)
        else:
            # Failed to get lock, queue next check
            build.task_id_check = None
            build.save()
            return "Failed to get lock on org.  {} has the org locked.  Queueing next check.".format(cache.get(lock_id))

@django_rq.job('short', timeout=60)
def check_queued_builds():
    reset_database_connection()

    from mrbelvedereci.build.models import Build
    builds = []
    for build in Build.objects.filter(status = 'queued', task_id_check__isnull = True).order_by('time_queue'):
        builds.append(build.id)
        res_check = check_queued_build.delay(build.id)
        build.task_id_check = res_check.id
        build.save()

    if builds:
        return 'Checked queued builds: {}'.format(', '.join(builds))
    else:
        return 'No queued builds to check'

@django_rq.job('short')
def set_github_status(build_id):
    reset_database_connection()

    from mrbelvedereci.build.models import Build
    build = Build.objects.get(id = build_id)
    create_status(build)

@django_rq.job('short')
def delete_scratch_orgs():
    reset_database_connection()

    from mrbelvedereci.cumulusci.models import ScratchOrgInstance
    orgs_deleted = 0
    orgs_failed = 0
    for org in ScratchOrgInstance.objects.filter(deleted = False, delete_error__isnull = False):
        org.delete_org()
        if org.deleted:
            orgs_deleted += 1
        else:
            orgs_failed += 1

    if not orgs_deleted and not orgs_failed:
        return 'No orgs found to delete'

    return 'Deleted {} orgs and failed to delete {} orgs'.format(orgs_deleted, orgs_failed)
