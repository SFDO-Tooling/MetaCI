from datetime import datetime
from django.dispatch.dispatcher import receiver

from django_rq import job
from django.utils.translation import gettext_lazy as _
from django.db.models.signals import post_delete, post_save

from metaci.release.models import Release, ReleaseCohort

from github3.repos.repo import Repository


@job("short")
def merge_freeze_job():
    """Determine if any merge freeze windows have started/stopped.
    If a window on a release cohort has started then we need to apply
    a failing merge freeze check to open pull requests in the repo.
    If a window on a release cohort has ended, then we need to apply a
    passing merge freeze check to all open pull requests."""
    now = datetime.now()

    # Signals will trigger the updating of merge freezes upon save.
    for rc in ReleaseCohort.objects.filter(
        status="Active", merge_freeze_end_date__lt=now
    ).all():
        rc.status = "Completed"
        rc.save()

    for rc in ReleaseCohort.objects.filter(
        status="Planned", merge_freeze_start_date__lt=now
    ).all():
        rc.status = "Active"
        rc.save()


def set_merge_freeze_status(repo: Repository, *, freeze: bool):
    # Get all open PRs in this repository
    for pr in repo.pull_requests(
        state="open", base=None
    ):  # TODO: set base to main branch
        # For each PR, get the head commit and apply the freeze status
        set_merge_freeze_status_for_commit(repo, pr.head.sha, freeze=freeze)


def set_merge_freeze_status_for_commit(repo: Repository, commit: str, freeze: bool):
    if freeze:
        state = "error"
        description = _("This repository is under merge freeze")
        target_url = ""  # TODO: the url of the release cohort view
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


@receiver(post_save, sender=ReleaseCohort)
def react_to_release_cohort_change(_sender, *, instance: ReleaseCohort, **kwargs):
    # We're interested in Release Cohort deletion and updates to the date-time fields and Status.
    # Cohort Creation alone won't trigger merge freeze (associating a Release to the Cohort will)

    # If the Release Cohort is currently in scope, add merge freeze on all of its repos.
    if instance.status == "Active":
        for release in instance.releases:
            set_merge_freeze_status(release.repo, freeze=True)
    else:
        # Otherwise, release any merge freezes that are safe to release.
        for release in instance.releases:
            release_merge_freeze_if_safe(release.repo)


@receiver(post_save, sender=Release)
def react_to_release_change(_sender, *, instance: Release, **kwargs):
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
def react_to_release_deletion(_sender, *, instance: Release, **kwargs):
    # This Release might have been moved from an in-scope release cohort to an out-of-scope Release Cohort or None
    # We don't know if this repo is also included in a different Release that might be in scope, so we can't
    # safely lift merge freeze until we check.

    release_merge_freeze_if_safe(instance.repo)


# TODO: bulkification
def release_merge_freeze_if_safe(repo: Repository):
    if not Release.objects.filter(repo=repo, release_cohort__status="Active").count():
        set_merge_freeze_status(repo, freeze=False)
