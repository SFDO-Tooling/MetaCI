from datetime import datetime
from datetime import timedelta

from django_rq import job

from metaci.release.models import ReleaseCohort

from github3.repos.repo import Repository


@job("short")
def merge_freeze_job() -> str:
    """Determine if any merge freeze windows have started/stopped.
    If a window on a release cohort has started then we need to apply
    a failing merge freeze check to open pull requests in the repo.
    If a window on a release cohort has ended, then we need to apply a
    passing merge freeze check to all open pull requests.


    repo a - in scope for both of the following cohorts
    c1 - ends today
    c2 - starts today
    """
    entered_scope = set()
    exited_scope = set()
    in_scope = set()
    cohorts = ReleaseCohort.objects.all()

    # First, we locate all repositories that have just entered scope for a merge freeze
    for cohort in cohorts:
        # Are the repos for this cohort currently in scope?
        if cohort.in_scope:
            in_scope.update(rel.repo for rel in cohort.releases.all())

            # Did this cohort _just_ enter scope?
            if (
                cohort.merge_freeze_start
                > (datetime.now() - timedelta(minutes=-8)).isoformat()
            ):
                entered_scope.update(rel.repo for rel in cohort.releases.all())

    # Next, we locate all repositories that
    #  a) just left scope for any cohort
    #  b) are not in scope for any remaining active cohort
    for cohort in cohorts:
        if (
            not cohort.in_scope
            and cohort.merge_freeze_end
            > (datetime.now() - timedelta(minutes=-8)).isoformat()
        ):
            exited_scope.update(
                rel.repo for rel in cohort.releases.all() if rel.repo not in in_scope
            )

    # We now have the minimal sets we need to take action upon to apply or remove merge freeze.
    if entered_scope:
        for repository in entered_scope:
            set_merge_freeze_status(repository, freeze=True)

    if exited_scope:
        for repository in exited_scope:
            set_merge_freeze_status(repository, freeze=False)


# TODO: implement
def set_merge_freeze_status(repo: Repository, *, freeze: bool):
    pass


# TODO: what is the type of the commit parameter?
# TODO: implement
def set_merge_freeze_status_for_commit(repo: Repository, commit: str, freeze: bool):
    pass
