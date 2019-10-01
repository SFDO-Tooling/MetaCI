import functools
import logging
import time
from collections import namedtuple

import django_rq
from django import db
from django.conf import settings
from django.core.cache import cache
from django.db import transaction

from metaci.build.autoscaling import get_autoscaler
from metaci.build.signals import build_complete
from metaci.cumulusci.models import Org, jwt_session, sf_session
from metaci.repository.utils import create_status

BUILD_TIMEOUT = 28800
ACTIVESCRATCHORGLIMITS_KEY = "metaci:activescratchorgs:limits"
SCHEDULER_KEY = "metaci:scheduler"

ActiveScratchOrgLimits = namedtuple("ActiveScratchOrgLimits", ["remaining", "max"])

logger = logging.getLogger(__name__)


def reset_database_connection():
    db.connection.close()


def scratch_org_limits():
    cached = cache.get(ACTIVESCRATCHORGLIMITS_KEY, None)
    if cached:
        return cached

    sfjwt = jwt_session(username=settings.SFDX_HUB_USERNAME)
    limits = sf_session(sfjwt).limits()["ActiveScratchOrgs"]
    value = ActiveScratchOrgLimits(remaining=limits["Remaining"], max=limits["Max"])
    # store it for 65 seconds, enough til the next tick. we may want to tune this
    cache.set(ACTIVESCRATCHORGLIMITS_KEY, value, 65)
    return value


@django_rq.job("default", timeout=BUILD_TIMEOUT)
def run_build(build_id):
    reset_database_connection()
    from metaci.build.models import Build

    try:
        build = Build.objects.get(id=build_id)
    except Build.DoesNotExist:
        time.sleep(1)
        build = Build.objects.get(id=build_id)
    org = build.org or Org.objects.get(name=build.plan.org, repo=build.repo)

    try:
        build.run()
        if settings.GITHUB_STATUS_UPDATES_ENABLED:
            res_status = set_github_status.delay(build_id)
            build.task_id_status_end = res_status.id

        build.save()

        build_complete.send(
            sender=build.__class__, build=build, status=build.get_status()
        )

    except Exception as e:
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
    finally:
        if org.lock_id:
            cache.delete(org.lock_id)

    check_waiting_builds.delay()

    return build.get_status()


def check_org_available(build):
    # Check for concurrency blocking
    try:
        org = build.org or Org.objects.get(name=build.plan.org, repo=build.repo)
    except Org.DoesNotExist:
        build.log = "Could not find org configuration for org {}".format(build.plan.org)
        build.set_status("error")
        build.save()
        return

    if org.scratch:
        # For scratch orgs, we don't need concurrency blocking logic,
        # but we need to check capacity
        if scratch_org_limits().remaining < settings.SCRATCH_ORG_RESERVE:
            build.log = "DevHub does not have enough capacity to start this build. Requeueing task."
            build.save()
            return
    else:
        # For persistent orgs, use the cache to lock the org
        status = cache.add(
            org.lock_id, "build-{}".format(build.id), timeout=BUILD_TIMEOUT
        )
        if not status:
            # Failed to get lock, queue next check
            build.log = "Waiting on build #{} to complete".format(
                cache.get(org.lock_id)
            )
            build.save()
            return False

    return True


def avoid_reentrance(key):
    def decorate(func):
        @functools.wraps(func)
        def wrapper(*args, **kw):
            has_lock = cache.add(key, 1)
            if not has_lock:
                return
            try:
                return func(*args, **kw)
            finally:
                cache.delete(key)

        return wrapper

    return decorate


@django_rq.job("short", timeout=60)
@avoid_reentrance(SCHEDULER_KEY)
def check_waiting_builds():
    """Build scheduler

    Responsible for:
    - Prioritizing queued builds
    - Starting as many builds as there are workers available to run
    - Scaling up to add workers when possible
    - Scaling down when the queue is empty

    It is triggered once a minute as well as after any build is created --
    but the avoid_reentrance decorator prevents it from running concurrently with itself.
    """
    reset_database_connection()

    from metaci.build.models import Build

    # Collect the builds that are ready to run
    # (i.e. there's an org available)
    # in order of priority and when they were queued
    count_checked = 0
    count_started = 0
    autoscaler = get_autoscaler()
    logger.info(
        f"Workers: {autoscaler.active_workers}, Builds: {autoscaler.active_builds}"
    )
    for build in Build.objects.filter(status="queued").order_by(
        "-priority", "time_queue"
    ):
        count_checked += 1
        if not check_org_available(build):
            continue

        # Start builds that are ready until we run out of worker slots
        # (if autoscaling is enabled, scale up when possible)
        autoscaler.allocate_worker(high_priority=bool(build.priority))
        if autoscaler.target_workers > autoscaler.active_builds:
            with transaction.atomic():
                try:
                    build.status = "running"
                    build.save()
                    run_build.delay(build.id)
                    count_started += 1
                    autoscaler.build_started()
                    logger.info(f"Starting build {build.id}")
                except Exception:
                    logger.exception(f"Failed to start build {build.id}")

    autoscaler.apply_formation()

    if count_checked:
        return "Started {} of {} queued builds".format(count_started, count_checked)
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

    return "Scheduled deletion attempts for {} orgs".format(count)


@django_rq.job("short")
def delete_scratch_org(org_instance_id):
    reset_database_connection()
    from metaci.cumulusci.models import ScratchOrgInstance

    try:
        org = ScratchOrgInstance.objects.get(id=org_instance_id)
    except ScratchOrgInstance.DoesNotExist:
        return "Failed: could not find ScratchOrgInstance with id {}".format(
            org_instance_id
        )

    org.delete_org()
    if org.deleted:
        return "Deleted org instance #{}".format(org.id)
    else:
        return "Failed to delete org instance #{}".format(org.id)
