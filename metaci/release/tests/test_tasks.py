import unittest
from datetime import datetime, timedelta, timezone

import pytest
from django.conf import settings
from django.urls.base import reverse

from metaci.build.models import BUILD_STATUSES
from metaci.fixtures.factories import (
    Build,
    BuildFactory,
    PlanFactory,
    PlanRepositoryFactory,
    ReleaseCohortFactory,
    ReleaseFactory,
    RepositoryFactory,
)
from metaci.release.models import Release, ReleaseCohort
from metaci.release.tasks import (
    _run_planrepo_for_release,
    _run_release_builds,
    _update_release_cohorts,
    release_merge_freeze_if_safe,
    set_merge_freeze_status,
)


@unittest.mock.patch("metaci.release.tasks.set_merge_freeze_status")
@pytest.mark.django_db
def test_run_planrepo_for_release(smfs_mock):
    plan = PlanFactory(name="Plan1", role="Release Test")
    repo = RepositoryFactory(name="PublicRepo")
    planrepo = PlanRepositoryFactory(plan=plan, repo=repo)
    release = ReleaseFactory(repo=repo, created_from_commit="abc")

    assert Build.objects.count() == 0
    assert release.status != Release.STATUS.inprogress

    _run_planrepo_for_release(release, planrepo)

    assert Build.objects.count() == 1
    assert release.status == Release.STATUS.inprogress


@unittest.mock.patch("metaci.release.tasks.set_merge_freeze_status")
@pytest.mark.django_db
def test_run_release_builds__failed_release_test(smfs_mock):
    plan = PlanFactory(name="Plan1", role="Release Test")
    repo = RepositoryFactory(name="PublicRepo")
    planrepo = PlanRepositoryFactory(plan=plan, repo=repo)
    cohort = ReleaseCohortFactory()
    release = ReleaseFactory(repo=repo, release_cohort=cohort)
    BuildFactory(
        release=release,
        repo=repo,
        plan=plan,
        planrepo=planrepo,
        status=BUILD_STATUSES.fail,
    )
    BuildFactory(
        release=release,
        repo=repo,
        plan=plan,
        planrepo=planrepo,
        status=BUILD_STATUSES.success,
    )

    _run_release_builds(release)

    assert release.status == Release.STATUS.failed
    assert release.error_message == "One or more release builds failed."
    assert cohort.status == ReleaseCohort.STATUS.failed
    assert cohort.error_message == "One or more releases failed."


@unittest.mock.patch("metaci.release.tasks.set_merge_freeze_status")
@pytest.mark.django_db
def test_run_release_builds__succeeded_release_test(smfs_mock):
    plan = PlanFactory(name="Plan1", role="Release Test")
    repo = RepositoryFactory(name="PublicRepo")
    planrepo = PlanRepositoryFactory(plan=plan, repo=repo)
    cohort = ReleaseCohortFactory()
    release = ReleaseFactory(repo=repo, release_cohort=cohort)
    BuildFactory(
        release=release,
        repo=repo,
        plan=plan,
        planrepo=planrepo,
        status=BUILD_STATUSES.success,
    )

    _run_release_builds(release)

    assert release.status == Release.STATUS.completed


@unittest.mock.patch("metaci.release.tasks.set_merge_freeze_status")
@pytest.mark.django_db
def test_run_release_builds__no_release_deploy(smfs_mock):
    cohort = ReleaseCohortFactory()
    release = ReleaseFactory(release_cohort=cohort)
    BuildFactory(release=release, status=BUILD_STATUSES.success)

    _run_release_builds(release)

    assert release.status == Release.STATUS.failed
    assert release.error_message == "No Upload Release plan is available"
    assert cohort.status == ReleaseCohort.STATUS.failed
    assert cohort.error_message == "One or more releases failed."


@unittest.mock.patch("metaci.release.tasks.set_merge_freeze_status")
@pytest.mark.django_db
def test_run_release_builds__succeeded_release_deploy__no_upload_release(smfs_mock):
    plan = PlanFactory(name="Plan1", role="Release Deploy")
    repo = RepositoryFactory(name="PublicRepo")
    planrepo = PlanRepositoryFactory(plan=plan, repo=repo, active=True)
    cohort = ReleaseCohortFactory()
    release = ReleaseFactory(repo=repo, release_cohort=cohort)
    BuildFactory(
        release=release,
        repo=repo,
        plan=plan,
        planrepo=planrepo,
        status=BUILD_STATUSES.success,
    )

    _run_release_builds(release)

    assert release.status == Release.STATUS.failed
    assert release.error_message == "No Upload Release plan is available"
    assert cohort.status == ReleaseCohort.STATUS.failed
    assert cohort.error_message == "One or more releases failed."


@unittest.mock.patch("metaci.release.tasks.set_merge_freeze_status")
@unittest.mock.patch("metaci.release.tasks._run_planrepo_for_release")
@pytest.mark.django_db
def test_run_release_builds__succeeded_release_deploy(rpr_mock, smfs_mock):
    plan1 = PlanFactory(name="Plan1", role="Release Deploy")
    repo = RepositoryFactory(name="PublicRepo")
    plan2 = PlanFactory(name="Plan2", role="Upload Release")
    planrepo1 = PlanRepositoryFactory(plan=plan1, repo=repo, active=True)
    planrepo2 = PlanRepositoryFactory(plan=plan2, repo=repo, active=True)
    cohort = ReleaseCohortFactory()
    release = ReleaseFactory(repo=repo, release_cohort=cohort)
    BuildFactory(
        release=release,
        repo=repo,
        plan=plan1,
        planrepo=planrepo1,
        status=BUILD_STATUSES.success,
    )

    _run_release_builds(release)

    rpr_mock.assert_called_once_with(release, planrepo2)


@unittest.mock.patch("metaci.release.tasks.set_merge_freeze_status")
@pytest.mark.django_db
def test_run_release_builds__failed_release_deploy(smfs_mock):
    plan1 = PlanFactory(name="Plan1", role="Release Deploy")
    repo = RepositoryFactory(name="PublicRepo")
    plan2 = PlanFactory(name="Plan2", role="Upload Release")
    planrepo1 = PlanRepositoryFactory(plan=plan1, repo=repo, active=True)
    PlanRepositoryFactory(plan=plan2, repo=repo, active=True)
    cohort = ReleaseCohortFactory()
    release = ReleaseFactory(repo=repo, release_cohort=cohort)
    BuildFactory(
        release=release,
        repo=repo,
        plan=plan1,
        planrepo=planrepo1,
        status=BUILD_STATUSES.fail,
    )

    _run_release_builds(release)

    assert release.status == Release.STATUS.failed
    assert release.error_message == "One or more release builds failed."
    assert cohort.status == ReleaseCohort.STATUS.failed
    assert cohort.error_message == "One or more releases failed."


@unittest.mock.patch("metaci.release.tasks.set_merge_freeze_status")
@unittest.mock.patch("metaci.release.tasks._run_planrepo_for_release")
@pytest.mark.django_db
def test_run_release_builds__unrun_release_deploy(rpr_mock, smfs_mock):
    repo = RepositoryFactory(name="PublicRepo")
    plan = PlanFactory(name="Plan1", role="Release Deploy")
    planrepo = PlanRepositoryFactory(plan=plan, repo=repo, active=True)
    cohort = ReleaseCohortFactory()
    release = ReleaseFactory(repo=repo, release_cohort=cohort)

    _run_release_builds(release)

    rpr_mock.assert_called_once_with(release, planrepo)


@unittest.mock.patch("metaci.release.tasks.set_merge_freeze_status")
@unittest.mock.patch("metaci.release.tasks._run_planrepo_for_release")
@pytest.mark.django_db
def test_run_release_builds__failed_release_no_action(rpr_mock, smfs_mock):
    repo = RepositoryFactory(name="PublicRepo")
    plan = PlanFactory(name="Plan1", role="Release Deploy")
    PlanRepositoryFactory(plan=plan, repo=repo, active=True)
    cohort = ReleaseCohortFactory()
    release = ReleaseFactory(
        repo=repo, release_cohort=cohort, status=Release.STATUS.failed
    )

    _run_release_builds(release)

    rpr_mock.assert_not_called()


@unittest.mock.patch("metaci.release.tasks.set_merge_freeze_status")
@unittest.mock.patch("metaci.release.tasks._run_planrepo_for_release")
@pytest.mark.django_db
def test_run_release_builds__succeeded_release_no_action(rpr_mock, smfs_mock):
    repo = RepositoryFactory(name="PublicRepo")
    plan = PlanFactory(name="Plan1", role="Release Deploy")
    PlanRepositoryFactory(plan=plan, repo=repo, active=True)
    cohort = ReleaseCohortFactory()
    release = ReleaseFactory(
        repo=repo, release_cohort=cohort, status=Release.STATUS.completed
    )

    _run_release_builds(release)

    rpr_mock.assert_not_called()


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
    cohort_started.status = ReleaseCohort.STATUS.planned
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
        target_url=settings.SITE_URL + reverse("cohort_list"),
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
    cohort.status = ReleaseCohort.STATUS.canceled
    cohort.save()
    release = ReleaseFactory(repo=RepositoryFactory())
    release.release_cohort = cohort
    release.save()

    cohort.status = ReleaseCohort.STATUS.active
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
    cohort.status = ReleaseCohort.STATUS.canceled
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
    canceled_cohort = ReleaseCohortFactory(status=ReleaseCohort.STATUS.canceled)
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
    canceled_cohort = ReleaseCohortFactory(status=ReleaseCohort.STATUS.canceled)
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
