from datetime import datetime
from datetime import timedelta
from typing import Set, Tuple
from django.dispatch.dispatcher import receiver

from django_rq import job
from django.utils.translation import gettext_lazy as _
from django.db.models.signals import post_delete, post_save

from metaci.release.models import Release, ReleaseCohort

from github3.repos.repo import Repository


@job("short")
def merge_freeze_job() -> str:
    """Determine if any merge freeze windows have started/stopped.
    If a window on a release cohort has started then we need to apply
    a failing merge freeze check to open pull requests in the repo.
    If a window on a release cohort has ended, then we need to apply a
    passing merge freeze check to all open pull requests."""

    entered_scope, exited_scope = get_scope_changes()

    # We now have the minimal sets we need to take action upon to apply or remove merge freeze.
    if entered_scope:
        for repository in entered_scope:
            set_merge_freeze_status(repository, freeze=True)

    if exited_scope:
        for repository in exited_scope:
            set_merge_freeze_status(repository, freeze=False)


def get_scope_changes() -> Tuple[Set[Repository], Set[Repository]]:
    entered_scope = set()
    exited_scope = set()
    in_scope = set()
    cohorts = ReleaseCohort.objects.all()

    now = datetime.now()

    # First, we locate all repositories that have just entered scope for a merge freeze,
    # and all repositories that are currently in scope for any freeze
    for cohort in cohorts:
        # Are the repos for this cohort currently in scope?
        if cohort.in_scope:
            in_scope.update(rel.repo for rel in cohort.releases.all())

            # Did this cohort _just_ enter scope?
            if cohort.merge_freeze_start > (now - timedelta(minutes=-8)):
                entered_scope.update(rel.repo for rel in cohort.releases.all())

    # Next, we locate all repositories that
    #  a) just left scope for any cohort
    #  b) are not in scope for any remaining active cohort
    for cohort in cohorts:
        if not cohort.in_scope and cohort.merge_freeze_end > (
            now - timedelta(minutes=-8)
        ):
            exited_scope.update(
                rel.repo for rel in cohort.releases.all() if rel.repo not in in_scope
            )

    return entered_scope, exited_scope


def set_merge_freeze_status(repo: Repository, *, freeze: bool):
    # Get all open PRs in this repository
    for pr in repo.pull_requests(state="open"):
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
    if instance.in_scope:
        for release in instance.releases:
            set_merge_freeze_status(release.repo, freeze=True)
    else:
        # Otherwise, release any merge freezes that are safe to release.
        for release in instance.releases:
            release_merge_freeze_if_safe(release.repo)


@receiver(post_delete, sender=ReleaseCohort)
def react_to_release_cohort_deletion(_sender, *, instance: ReleaseCohort, **kwargs):
    # When a Release Cohort is deleted, we should lify merge freeze on any repos
    # that are not in scope for a different Release Cohort.
    for release in instance.releases:
        release_merge_freeze_if_safe(release.repo)


@receiver(post_save, sender=Release)
def react_to_release_change(_sender, *, instance: Release, **kwargs):
    # Right now, there's no way to cancel a single Release within a Release Cohort
    # (except for deleting the Release object)
    # We need to know if the relationship to Release Cohort changed.

    if kwargs.get("created", False):
        # There is no case where Release creation would lead to lifting merge freeze.
        if instance.release_cohort and instance.release_cohort.in_scope:
            # Set merge freeze to on for this Release's Repository
            set_merge_freeze_status(instance.repo, freeze=True)
    else:
        # A Release was updated - we only care if the Release Cohort lookup was changed.
        if instance.release_cohort and instance.release_cohort.in_scope:
            # Set merge freeze to on for this Release's Repository
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
    for r in Release.objects.filter(repo=repo, release_cohort__ne=None).all():
        if r.release_cohort.in_scope:  # TODO: fold into query
            # Merge freeze is already on - we cannot turn it off.
            return

    set_merge_freeze_status(repo, freeze=False)
