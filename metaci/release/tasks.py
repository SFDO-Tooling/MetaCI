from datetime import datetime, timezone
from django.dispatch.dispatcher import receiver

from django_rq import job
from django.conf import settings
from django.utils.translation import gettext as _
from django.urls import reverse
from django.db.models.signals import post_delete, post_save

from metaci.release.models import Release, ReleaseCohort
from metaci.repository.models import Repository

from github3.repos.repo import Repository as GitHubRepository


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
