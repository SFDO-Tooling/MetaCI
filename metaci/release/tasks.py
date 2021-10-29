from collections import defaultdict
from datetime import datetime, timezone
import operator
from typing import List
from django.db.models.query import QuerySet

from django.dispatch.dispatcher import receiver

from django_rq import job
from django.conf import settings
from django.utils.translation import gettext as _
from django.urls import reverse
from django.db.models.signals import post_delete, post_save
from metaci.build.models import BUILD_STATUSES, Build
from metaci.plan.models import PlanRepository

from metaci.release.models import Release, ReleaseCohort
from metaci.repository.models import Repository

from github3.repos.repo import Repository as GitHubRepository


def _run_planrepo_for_release(release: Release, planrepo: PlanRepository):
    build = Build(
        repo=release.repo,
        plan=planrepo.plan,
        planrepo=planrepo,
        commit=release.created_from_commit,
        build_type="auto",
        release=release,
        release_relationship_type="automation",
    )
    build.save()
    if release.status != Release.STATUS.inprogress:
        release.status = Release.STATUS.inprogress
        release.save()


def find_active_planrepos(release: Release, role: str) -> QuerySet[PlanRepository]:
    return release.repo.planrepos.filter(plan__role=role, active=True)


def _run_release_builds(release: Release):
    FAILED_STATUSES = [BUILD_STATUSES.error, BUILD_STATUSES.fail]
    COMPLETED_STATUSES = [BUILD_STATUSES.success, *FAILED_STATUSES]

    def running(builds: List[Build]) -> bool:
        return bool(builds) and not all(b.status in COMPLETED_STATUSES for b in builds)

    def succeeded(builds: List[Build]) -> bool:
        return (
            bool(builds)
            and not running(builds)
            and builds[-1].status == BUILD_STATUSES.success
        )

    def failed(builds: List[Build]) -> bool:
        return (
            bool(builds)
            and not running(builds)
            and builds[-1].status in FAILED_STATUSES
        )

    def any_failed(builds: List[Build]) -> bool:
        return bool(builds) and any(b.status in FAILED_STATUSES for b in builds)

    if release.status in [Release.STATUS.failed, Release.STATUS.completed]:
        # Release manager must manually set the status back to In Progress if they're attempting
        # to retry any failed builds.
        return

    # Locate builds associated with this Release.
    builds = defaultdict(list)
    for build in release.builds.all():
        if build.plan.role in ["Upload Release", "Release Deploy", "Release Test"]:
            builds[build.plan.role].append(build)

    # Sort Builds so that we can find the latest of each Role.
    # This supports multi-build retries (rather than rerunning a single Build).
    # Note that our predicates (succeeded() et al.) check for running builds
    # and return False if builds are still running, which is why we can
    # reasonably use `time_end`.
    for plan_role in ["Upload Release", "Release Deploy", "Release Test"]:
        builds[plan_role] = sorted(
            builds[plan_role], key=operator.attrgetter("time_end")
        )

    # Determine what state we are in.

    # Release Test is running or has run.
    if builds["Release Test"]:
        if succeeded(builds["Release Test"]):
            release.status = Release.STATUS.completed
        if any_failed(builds["Release Test"]):
            # Plans may run multiple builds with the role Release Test
            # All of them must pass.
            release.status = Release.STATUS.failed
            release.error_message = "One or more release builds failed."

        release.save()
        return

    has_release_deploy = bool(find_active_planrepos(release, "Release Deploy"))

    # We ran, or do not have, Release Deploy and need to run Upload Release.
    if not builds["Upload Release"] and (
        not has_release_deploy or builds["Release Deploy"]
    ):
        if not has_release_deploy or succeeded(builds["Release Deploy"]):
            # Locate the Upload Release plan and planrepo.
            upload_release_planrepos = find_active_planrepos(release, "Upload Release")
            if upload_release_planrepos.count() == 0:
                release.error_message = _("No Upload Release plan is available")
                release.save()
                return

            upload_release_planrepo = upload_release_planrepos.first()

            _run_planrepo_for_release(release, upload_release_planrepo)
            return
        elif has_release_deploy and failed(builds["Release Deploy"]):
            release.status = Release.STATUS.failed
            release.error_message = "One or more release builds failed."
            release.save()
            return

    # We have a Release Deploy build and it has not yet run.
    if has_release_deploy and not builds["Release Deploy"]:
        _run_planrepo_for_release(
            release, find_active_planrepos(release, "Release Deploy").first()
        )
        release.status = Release.STATUS.inprogress
        release.save()

    # The release is running - no new builds required.


@job
def update_cohort_status() -> str:
    """Run every minute to update Release Cohorts to Active once they pass their start date
    and to Completed once they pass their start date."""

    return _update_release_cohorts()


def _update_release_cohorts() -> str:
    now = datetime.now(tz=timezone.utc)

    # Signals will trigger the updating of merge freezes upon save.
    names_ended = []
    for rc in ReleaseCohort.objects.filter(
        status="Active", merge_freeze_end__lt=now
    ).all():
        rc.status = "Completed"
        rc.save()
        names_ended.append(rc.name)

    names_started = []
    for rc in ReleaseCohort.objects.filter(
        status="Planned", merge_freeze_start__lt=now, merge_freeze_end__gt=now
    ).all():
        rc.status = "Active"
        rc.save()
        names_started.append(rc.name)

    return f"Enabled merge freeze on {', '.join(names_started)} and ended merge freeze on {', '.join(names_ended)}."


def set_merge_freeze_status(repo: Repository, *, freeze: bool):
    # Get all open PRs in this repository
    github_repo = repo.get_github_api()
    for pr in github_repo.pull_requests(state="open", base=github_repo.default_branch):
        # For each PR, get the head commit and apply the freeze status
        set_merge_freeze_status_for_commit(github_repo, pr.head.sha, freeze=freeze)


def set_merge_freeze_status_for_commit(
    repo: GitHubRepository, commit: str, *, freeze: bool
):
    if freeze:
        state = "error"
        description = _("This repository is under merge freeze.")
        target_url = settings.SITE_URL + reverse("cohort_list")
    else:
        state = "success"
        description = ""
        target_url = ""

    repo.create_status(
        sha=commit,
        state=state,
        target_url=target_url,
        description=description,
        context=_("Merge Freeze"),
    )


def release_merge_freeze_if_safe(repo: Repository):
    if not Release.objects.filter(repo=repo, release_cohort__status="Active").count():
        set_merge_freeze_status(repo, freeze=False)


@receiver(post_save, sender=ReleaseCohort)
def react_to_release_cohort_change(instance: ReleaseCohort, **kwargs):
    # We're interested in Release Cohort deletion and updates to the date-time fields and Status.
    # Cohort Creation alone won't trigger merge freeze (associating a Release to the Cohort will)

    # If the Release Cohort is currently in scope, add merge freeze on all of its repos.
    if instance.status == "Active":
        for release in instance.releases.all():
            set_merge_freeze_status(release.repo, freeze=True)
    else:
        # Otherwise, release any merge freezes that are safe to release.
        for release in instance.releases.all():
            release_merge_freeze_if_safe(release.repo)


@receiver(post_save, sender=Release)
def react_to_release_change(instance: Release, **kwargs):
    # Right now, there's no way to cancel a single Release within a Release Cohort
    # (except for deleting the Release object)
    # We need to know if the relationship to Release Cohort changed.

    if kwargs.get("created", False):
        # There is no case where Release creation would lead to lifting merge freeze.
        if instance.release_cohort and instance.release_cohort.status == "Active":
            set_merge_freeze_status(instance.repo, freeze=True)
    else:
        # A Release was updated - if it was added to an in-scope Cohort, set merge freeze.
        if instance.release_cohort and instance.release_cohort.status == "Active":
            set_merge_freeze_status(instance.repo, freeze=True)
        else:
            # This Release might have been moved from an in-scope release cohort to an out-of-scope Release Cohort or None
            # We don't know if this repo is also included in a different Release that might be in scope, so we can't
            # safely lift merge freeze until we check.
            release_merge_freeze_if_safe(instance.repo)


@receiver(post_delete, sender=Release)
def react_to_release_deletion(instance: Release, **kwargs):
    # This Release might have been moved from an in-scope release cohort to an out-of-scope Release Cohort or None
    # We don't know if this repo is also included in a different Release that might be in scope, so we can't
    # safely lift merge freeze until we check.

    release_merge_freeze_if_safe(instance.repo)
