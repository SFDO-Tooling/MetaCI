from datetime import datetime, timezone, timedelta
import unittest

from django.urls.base import reverse

from metaci.fixtures.factories import (
    ReleaseCohortFactory,
    ReleaseFactory,
    RepositoryFactory,
)
from metaci.release.tasks import (
    _update_release_cohorts,
    release_merge_freeze_if_safe,
    set_merge_freeze_status_for_commit,
    set_merge_freeze_status,
)

import pytest


@pytest.mark.django_db
def test_update_release_cohorts():
    cohort_ended = ReleaseCohortFactory()
    cohort_ended.merge_freeze_end = datetime.now(tz=timezone.utc) - timedelta(
        minutes=20
    )
    cohort_ended.save()

    cohort_started = ReleaseCohortFactory()
    cohort_started.merge_freeze_start = datetime.now(tz=timezone.utc) - timedelta(
        minutes=20
    )
    cohort_started.merge_freeze_end = datetime.now(tz=timezone.utc) + timedelta(
        minutes=20
    )
    cohort_started.status = "Planned"
    cohort_started.save()

    assert (
        _update_release_cohorts()
        == f"Enabled merge freeze on {cohort_started.name} and ended merge freeze on {cohort_ended.name}."
    )


def test_set_merge_freeze_status__on():
    repo = unittest.mock.Mock()
    repo.get_github_api.return_value.pull_requests.return_value = [unittest.mock.Mock()]

    set_merge_freeze_status(repo, freeze=True)

    pr = repo.get_github_api.return_value.pull_requests.return_value[0]
    repo.get_github_api.return_value.create_status.assert_called_once_with(
        sha=pr.head.sha,
        state="error",
        target_url=reverse("cohort_list"),
        description="This repository is under merge freeze.",
        context="Merge Freeze",
    )


def test_set_merge_freeze_status__off():
    repo = unittest.mock.Mock()
    repo.get_github_api.return_value.pull_requests.return_value = [unittest.mock.Mock()]

    set_merge_freeze_status(repo, freeze=False)

    pr = repo.get_github_api.return_value.pull_requests.return_value[0]
    repo.get_github_api.return_value.create_status.assert_called_once_with(
        sha=pr.head.sha,
        state="success",
        target_url="",
        description="",
        context="Merge Freeze",
    )


@unittest.mock.patch("metaci.release.tasks.release_merge_freeze_if_safe")
@unittest.mock.patch("metaci.release.tasks.set_merge_freeze_status")
@pytest.mark.django_db
def test_react_to_release_cohort_change__activate(smfs_mock, rmfs_mock):
    cohort = ReleaseCohortFactory()
    cohort.status = "Canceled"
    cohort.save()
    release = ReleaseFactory(repo=RepositoryFactory())
    release.release_cohort = cohort
    release.save()

    cohort.status = "Active"
    cohort.save()

    # release_merge_freeze_if_safe() will also be called once,
    # when we associate the Release to a Canceled Cohort.
    # That is not under test here.
    smfs_mock.assert_called_once_with(release.repo, freeze=True)


@unittest.mock.patch("metaci.release.tasks.release_merge_freeze_if_safe")
@unittest.mock.patch("metaci.release.tasks.set_merge_freeze_status")
@pytest.mark.django_db
def test_react_to_release_cohort_change__deactivate(smfs_mock, rmfs_mock):
    cohort = ReleaseCohortFactory()
    release = ReleaseFactory(repo=RepositoryFactory())
    release.release_cohort = cohort
    release.save()
    cohort.status = "Canceled"
    cohort.save()

    # Note: set_merge_freeze_status() will also be called once,
    # when the release is associated with the cohort,
    # but that's not under test here.
    rmfs_mock.assert_called_once_with(release.repo)


@unittest.mock.patch("metaci.release.tasks.set_merge_freeze_status")
@pytest.mark.django_db
def test_react_to_release_change__created_active(smfs_mock):
    cohort = ReleaseCohortFactory()
    release = ReleaseFactory(repo=RepositoryFactory())
    release.release_cohort = cohort
    release.save()

    smfs_mock.assert_called_once_with(release.repo, freeze=True)


@pytest.mark.django_db
@unittest.mock.patch("metaci.release.tasks.release_merge_freeze_if_safe")
def test_react_to_release_change__moved_active(rmfs_mock):
    canceled_cohort = ReleaseCohortFactory(status="Canceled")
    cohort = ReleaseCohortFactory()
    release = ReleaseFactory(repo=RepositoryFactory(), release_cohort=canceled_cohort)

    with unittest.mock.patch(
        "metaci.release.tasks.set_merge_freeze_status"
    ) as smfs_mock:
        release.release_cohort = cohort
        release.save()

        smfs_mock.assert_called_once_with(release.repo, freeze=True)


@pytest.mark.django_db
@unittest.mock.patch("metaci.release.tasks.set_merge_freeze_status")
def test_react_to_release_change__moved_inactive(smfs_mock):
    canceled_cohort = ReleaseCohortFactory(status="Canceled")
    cohort = ReleaseCohortFactory()
    release = ReleaseFactory(repo=RepositoryFactory(), release_cohort=cohort)

    with unittest.mock.patch(
        "metaci.release.tasks.release_merge_freeze_if_safe"
    ) as rmfs_mock:
        release.release_cohort = canceled_cohort
        release.save()

        rmfs_mock.assert_called_once_with(release.repo)


@pytest.mark.django_db
@unittest.mock.patch("metaci.release.tasks.release_merge_freeze_if_safe")
@unittest.mock.patch("metaci.release.tasks.set_merge_freeze_status")
def test_react_to_release_deletion(smfs_mock, rmfs_mock):
    cohort = ReleaseCohortFactory()
    release = ReleaseFactory(repo=RepositoryFactory(), release_cohort=cohort)

    release.delete()
    rmfs_mock.assert_called_once_with(release.repo)


@unittest.mock.patch("metaci.release.tasks.set_merge_freeze_status")
@pytest.mark.django_db
def test_release_merge_freeze_if_safe__not_safe(smfs_mock):
    cohort = ReleaseCohortFactory()
    release = ReleaseFactory(repo=RepositoryFactory(), release_cohort=cohort)
    smfs_mock.reset_mock()

    release_merge_freeze_if_safe(release.repo)

    smfs_mock.assert_not_called()


@unittest.mock.patch("metaci.release.tasks.set_merge_freeze_status")
@pytest.mark.django_db
def test_release_merge_freeze_if_safe__safe(smfs_mock):
    release = ReleaseFactory(repo=RepositoryFactory())

    release_merge_freeze_if_safe(release.repo)

    smfs_mock.assert_called_once_with(release.repo, freeze=False)
