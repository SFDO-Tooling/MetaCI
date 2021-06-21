import time
import traceback
import typing as T
from collections import namedtuple

import django_rq
from cumulusci.core.utils import import_global
from cumulusci.oauth.salesforce import jwt_session
from django import db
from django.conf import settings
from django.core.cache import cache
from django.utils import timezone
from rq.exceptions import ShutDownImminentException

from metaci.build.autoscaling import autoscale
from metaci.build.exceptions import RequeueJob
from metaci.build.signals import build_complete
from metaci.build.utils import set_build_info
from metaci.cumulusci.models import Org, sf_session
from metaci.repository.utils import create_status

ACTIVESCRATCHORGLIMITS_KEY = "metaci:activescratchorgs:limits"

ActiveScratchOrgLimits = namedtuple("ActiveScratchOrgLimits", ["remaining", "max"])


def reset_database_connection():
    db.connection.close()


def scratch_org_limits():
    cached = cache.get(ACTIVESCRATCHORGLIMITS_KEY, None)
    if cached:
        return cached

    sfjwt = jwt_session(
        settings.SFDX_CLIENT_ID, settings.SFDX_HUB_KEY, settings.SFDX_HUB_USERNAME
    )
    limits = sf_session(sfjwt).limits()["ActiveScratchOrgs"]
    value = ActiveScratchOrgLimits(remaining=limits["Remaining"], max=limits["Max"])
    # store it for 65 seconds, enough til the next tick. we may want to tune this
    cache.set(ACTIVESCRATCHORGLIMITS_KEY, value, 65)
    return value


def run_build(build_id, lock_id=None):
    reset_database_connection()
    from metaci.build.models import Build

    try:
        build = Build.objects.get(id=build_id)
    except Build.DoesNotExist:
        time.sleep(1)
        build = Build.objects.get(id=build_id)

    try:
        build.run()
        if settings.GITHUB_STATUS_UPDATES_ENABLED:
            res_status = set_github_status.delay(build_id)
            build.task_id_status_end = res_status.id

        build.save()

        build_complete.send(
            sender=build.__class__, build=build, status=build.get_status()
        )

    except ShutDownImminentException:
        # The Heroku dyno is restarting.
        # Log that, leave the build's status as running,
        # and let the exception fall through to the rq worker to requeue the job.
        build.log += (
            "\nERROR: Build aborted because the Heroku dyno restarted. "
            "MetaCI will try to start a rebuild."
        )
        build.save()
        raise RequeueJob
    except Exception as e:
        if lock_id:
            cache.delete(lock_id)
        if settings.GITHUB_STATUS_UPDATES_ENABLED:
            res_status = set_github_status.delay(build_id)
            build.task_id_status_end = res_status.id

        build.set_status("error")
        build.log += "\nERROR: The build raised an exception\n"
        build.log += str(e)
        build.save()

        build_complete.send(
            sender=build.__class__, build=build, status=build.get_status()
        )

    if lock_id:
        cache.delete(lock_id)

    return build.get_status()


def dispatch_build(build, lock_id: str = None):
    queue_name = build.plan.queue
    if queue_name == "long-running":
        return dispatch_one_off_build(build, lock_id)
    else:
        return dispatch_queued_build(build, lock_id)


def dispatch_one_off_build(build, lock_id: str = None):
    # parent functions are expecting something in this
    # shape
    class Result(T.NamedTuple):
        id: T.Any

    try:
        job_id = launch_one_off_build_worker(build, lock_id)
        build.log = build.log or ""
        build.log += f"\nRunning build in context (dyno) {job_id}\n"
        build.save()
    except Exception as e:
        set_build_info(
            build,
            status="error",
            time_end=timezone.now(),
            error_message=str(e),
            exception=e.__class__.__name__,
            traceback="".join(traceback.format_tb(e.__traceback__)),
        )
        raise e
    return Result(job_id)


def dispatch_queued_build(build, lock_id: str = None):
    queue = django_rq.get_queue(build.plan.queue)
    result = queue.enqueue(
        run_build, build.id, lock_id, job_timeout=build.plan.build_timeout
    )
    build.task_id_check = None
    build.task_id_run = result.id
    build.save()
    autoscale()
    return result


def lock_org(org, build_id, timeout):
    return cache.add(org.lock_id, f"build-{build_id}", timeout=timeout)


@django_rq.job("short", timeout=60)
def check_queued_build(build_id):
    reset_database_connection()

    from metaci.build.models import Build

    try:
        build = Build.objects.get(id=build_id)
    except Build.DoesNotExist:
        time.sleep(1)
        build = Build.objects.get(id=build_id)

    # Check for concurrency blocking
    try:
        org = build.org or Org.objects.get(name=build.plan.org, repo=build.repo)
    except Org.DoesNotExist:
        message = f"Could not find org configuration for org {build.plan.org}"
        build.log = message
        build.set_status("error")
        build.save()
        return message

    if org.scratch:
        # For scratch orgs, we don't need concurrency blocking logic,
        # but we need to check capacity

        if scratch_org_limits().remaining < settings.SCRATCH_ORG_RESERVE:
            build.task_id_check = None
            build.set_status("waiting")
            msg = "DevHub does not have enough capacity to start this build. Requeueing task."
            build.log = msg
            build.save()
            return msg
        res_run = dispatch_build(build)
        return (
            "DevHub has scratch org capacity, running the build "
            + f"as task {res_run.id}"
        )
    else:
        # For persistent orgs, use the cache to lock the org
        status = lock_org(org, build_id, build.plan.build_timeout)

        if status is True:
            # Lock successful, run the build
            res_run = dispatch_build(build, org.lock_id)
            return f"Got a lock on the org, running as task {res_run.id}"
        else:
            # Failed to get lock, queue next check
            build.task_id_check = None
            build.set_status("waiting")
            build.log = f"Waiting on build #{cache.get(org.lock_id)} to complete"
            build.save()
            return (
                "Failed to get lock on org. "
                + f"{cache.get(org.lock_id)} has the org locked. Queueing next check."
            )


@django_rq.job("short", timeout=60)
def check_waiting_builds():
    reset_database_connection()

    from metaci.build.models import Build

    builds = []
    for build in Build.objects.filter(status="waiting").order_by("time_queue"):
        builds.append(build.id)
        res_check = check_queued_build.delay(build.id)
        build.task_id_check = res_check.id
        build.save()

    if builds:
        return f"Checked waiting builds: {builds}"
    else:
        return "No queued builds to check"


@django_rq.job("short")
def set_github_status(build_id):
    reset_database_connection()

    from metaci.build.models import Build

    build = Build.objects.get(id=build_id)
    create_status(build)


@django_rq.job("short")
def delete_scratch_orgs():
    reset_database_connection()

    from metaci.cumulusci.models import ScratchOrgInstance

    count = 0
    for org in ScratchOrgInstance.objects.filter(
        deleted=False, delete_error__isnull=False
    ):
        delete_scratch_org.delay(org.id)
        count += 1

    if not count:
        return "No orgs found to delete"

    return f"Scheduled deletion attempts for {count} orgs"


@django_rq.job("short")
def delete_scratch_org(org_instance_id):
    reset_database_connection()
    from metaci.cumulusci.models import ScratchOrgInstance

    try:
        org = ScratchOrgInstance.objects.get(id=org_instance_id)
    except ScratchOrgInstance.DoesNotExist:
        return f"Failed: could not find ScratchOrgInstance with id {org_instance_id}"

    org.delete_org()
    if org.deleted:
        return f"Deleted org instance #{org.id}"
    else:
        return f"Failed to delete org instance #{ord.id}"


def launch_one_off_build_worker(build, lock_id: str):
    """Immediately launch a one-off-build with env-appropriate autoscaler"""
    config = settings.METACI_LONG_RUNNING_BUILD_CONFIG
    assert isinstance(
        config, dict
    ), "METACI_LONG_RUNNING_BUILD_CONFIG should be a JSON-format dict"
    autoscaler_class = import_global(settings.METACI_LONG_RUNNING_BUILD_CLASS)
    autoscaler = autoscaler_class(config)
    try:
        return autoscaler.one_off_build(build.id, lock_id)
    except Exception as e:
        raise AssertionError(f"Cannot create one-off-build {e}") from e
