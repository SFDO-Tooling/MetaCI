import os
import time

from django import db
from django.conf import settings
from django.core.cache import cache
import django_rq
import requests

from mrbelvedereci.build.signals import build_complete
from mrbelvedereci.cumulusci.models import Org
from mrbelvedereci.repository.utils import create_status

BUILD_TIMEOUT = 28800


def reset_database_connection():
    db.connection.close()


@django_rq.job('default', timeout=BUILD_TIMEOUT)
def run_build(build_id, lock_id=None):
    reset_database_connection()
    from mrbelvedereci.build.models import Build
    try:
        build = Build.objects.get(id=build_id)
    except Build.DoesNotExist:
        time.sleep(1)
        build = Build.objects.get(id=build_id)

    try:
        exception = None
        build.run()
        if settings.GITHUB_STATUS_UPDATES_ENABLED:
            res_status = set_github_status.delay(build_id)
            build.task_id_status_end = res_status.id

        build.save()

        build_complete.send(
            sender=build.__class__,
            build=build,
            status=build.get_status(),
        )

    except Exception as e:
        if lock_id:
            cache.delete(lock_id)
        if settings.GITHUB_STATUS_UPDATES_ENABLED:
            res_status = set_github_status.delay(build_id)
            build.task_id_status_end = res_status.id

        build.set_status('error')
        build.log += '\nERROR: The build raised an exception\n'
        build.log += unicode(e)
        build.save()

        build_complete.send(
            sender=build.__class__,
            build=build,
            status=build.get_status(),
        )

    if lock_id:
        cache.delete(lock_id)

    return build.get_status()


@django_rq.job('short', timeout=60)
def check_queued_build(build_id):
    reset_database_connection()

    from mrbelvedereci.build.models import Build
    build = Build.objects.get(id=build_id)

    # Check for concurrency blocking
    try:
        org = Org.objects.get(name=build.plan.org, repo=build.repo)
    except Org.DoesNotExist:
        message = 'Could not find org configuration for org {}'.format(
            build.plan.org)
        build.log = message
        build.set_status('error')
        build.save()
        return 'Could not find org configuration for org {}'.format(
            build.plan.org)

    if org.scratch:
        # For scratch orgs, we don't need concurrency blocking logic, just run
        # the build
        res_run = run_build.delay(build.id)
        build.task_id_check = None
        build.task_id_run = res_run.id
        build.save()
        return ('Org is a scratch org, running build concurrently ' +
                'as task {}'.format(res_run.id))

    else:
        # For persistent orgs, use the cache to lock the org
        status = cache.add(
            org.lock_id,
            'build-{}'.format(build_id),
            timeout=BUILD_TIMEOUT,
        )

        if status is True:
            # Lock successful, run the build
            res_run = run_build.delay(build.id, org.lock_id)
            build.task_id_run = res_run.id
            build.save()
            return 'Got a lock on the org, running as task {}'.format(
                res_run.id)
        else:
            # Failed to get lock, queue next check
            build.task_id_check = None
            build.set_status('waiting')
            build.log = 'Waiting on build #{} to complete'.format(
                cache.get(org.lock_id))
            build.save()
            return ('Failed to get lock on org. ' +
                    '{} has the org locked. Queueing next check.'.format(
                        cache.get(org.lock_id)))


@django_rq.job('short', timeout=60)
def check_waiting_builds():
    reset_database_connection()

    from mrbelvedereci.build.models import Build
    builds = []
    for build in Build.objects.filter(status='waiting').order_by('time_queue'):
        builds.append(build.id)
        res_check = check_queued_build.delay(build.id)
        build.task_id_check = res_check.id
        build.save()

    if builds:
        return 'Checked waiting builds: {}'.format(builds)
    else:
        return 'No queued builds to check'


@django_rq.job('short')
def set_github_status(build_id):
    reset_database_connection()

    from mrbelvedereci.build.models import Build
    build = Build.objects.get(id=build_id)
    create_status(build)


@django_rq.job('short')
def delete_scratch_orgs():
    reset_database_connection()

    from mrbelvedereci.cumulusci.models import ScratchOrgInstance
    count = 0
    for org in ScratchOrgInstance.objects.filter(deleted=False,
                                                 delete_error__isnull=False):
        delete_scratch_org.delay(org.id)
        count += 1

    if not count:
        return 'No orgs found to delete'

    return 'Scheduled deletion attempts for {} orgs'.format(count)


@django_rq.job('short')
def delete_scratch_org(org_instance_id):
    reset_database_connection()
    from mrbelvedereci.cumulusci.models import ScratchOrgInstance
    try:
        org = ScratchOrgInstance.objects.get(id=org_instance_id)
    except ScratchOrgInstance.DoesNotExist:
        return 'Failed: could not find ScratchOrgInstance with id {}'.format(
            org_instance_id)

    org.delete_org()
    if org.deleted:
        return 'Deleted org instance #{}'.format(org.id)
    else:
        return 'Failed to delete org instance #{}'.format(org.id)
