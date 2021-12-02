import unittest
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from unittest.mock import Mock, call

import pytest
from cumulusci.core.dependencies.dependencies import (
    GitHubDynamicDependency,
    UnmanagedGitHubRefDependency,
)
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
    DependencyGraphError,
    NonProjectConfig,
    _run_planrepo_for_release,
    _run_release_builds,
    _update_release_cohorts,
    advance_releases,
    all_deps_satisfied,
    create_dependency_tree,
    execute_active_release_cohorts,
    get_dependency_graph,
    release_merge_freeze_if_safe,
    set_merge_freeze_status,
)


@unittest.mock.patch("metaci.release.tasks.set_merge_freeze_status")
@pytest.mark.django_db
def test_run_planrepo_for_release(smfs_mock):
    plan = PlanFactory(name="Plan1", role="release_test")
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
    plan = PlanFactory(name="Plan1", role="release_test")
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
def test_run_release_builds__failed_release_test__no_cohort(smfs_mock):
    plan = PlanFactory(name="Plan1", role="release_test")
    repo = RepositoryFactory(name="PublicRepo")
    planrepo = PlanRepositoryFactory(plan=plan, repo=repo)
    release = ReleaseFactory(repo=repo)
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
    assert release.release_cohort is None


@unittest.mock.patch("metaci.release.tasks.set_merge_freeze_status")
@pytest.mark.django_db
def test_run_release_builds__succeeded_release_test(smfs_mock):
    plan = PlanFactory(name="Plan1", role="release_test")
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
    assert release.error_message == "No 'Release' plan is available"
    assert cohort.status == ReleaseCohort.STATUS.failed
    assert cohort.error_message == "One or more releases failed."


@unittest.mock.patch("metaci.release.tasks.set_merge_freeze_status")
@pytest.mark.django_db
def test_run_release_builds__succeeded_release_deploy__no_upload_release(smfs_mock):
    plan = PlanFactory(name="Plan1", role="release_deploy")
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
    assert release.error_message == "No 'Release' plan is available"
    assert cohort.status == ReleaseCohort.STATUS.failed
    assert cohort.error_message == "One or more releases failed."


@unittest.mock.patch("metaci.release.tasks.set_merge_freeze_status")
@unittest.mock.patch("metaci.release.tasks._run_planrepo_for_release")
@pytest.mark.django_db
def test_run_release_builds__succeeded_release_deploy(rpr_mock, smfs_mock):
    plan1 = PlanFactory(name="Plan1", role="release_deploy")
    repo = RepositoryFactory(name="PublicRepo")
    plan2 = PlanFactory(name="Plan2", role="release")
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
    plan1 = PlanFactory(name="Plan1", role="release_deploy")
    repo = RepositoryFactory(name="PublicRepo")
    plan2 = PlanFactory(name="Plan2", role="release")
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
    plan = PlanFactory(name="Plan1", role="release_deploy")
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
    plan = PlanFactory(name="Plan1", role="release_deploy")
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
    plan = PlanFactory(name="Plan1", role="release_deploy")
    PlanRepositoryFactory(plan=plan, repo=repo, active=True)
    cohort = ReleaseCohortFactory()
    release = ReleaseFactory(
        repo=repo, release_cohort=cohort, status=Release.STATUS.completed
    )

    _run_release_builds(release)

    rpr_mock.assert_not_called()


@pytest.mark.django_db
def test_update_release_cohorts():
    cohort_started = ReleaseCohortFactory()
    cohort_started.merge_freeze_start = datetime.now(tz=timezone.utc) - timedelta(
        minutes=20
    )
    cohort_started.merge_freeze_end = datetime.now(tz=timezone.utc) + timedelta(
        minutes=20
    )
    cohort_started.status = ReleaseCohort.STATUS.approved
    cohort_started.save()

    assert (
        _update_release_cohorts() == f"Enabled merge freeze on {cohort_started.name}."
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


def test_all_deps_satisfied():
    a = Mock()
    b = Mock()
    c = Mock()

    # Build a mock release tree where the middle link (b)
    # is not being released in this Cohort.
    # C depends on B depends on A.
    a.repo.url = "foo"
    b.repo.url = "bar"
    c.repo.url = "spam"
    a.status = Release.STATUS.completed
    c.status = Release.STATUS.blocked

    # Build the dependency graph, a map from GitHub URL
    # to a set of dependency GitHub URLs.
    graph = defaultdict(list)
    graph[b.repo.url].append(a.repo.url)
    graph[c.repo.url].append(b.repo.url)

    # We only have releases for A and C. We're asking,
    # "Is C ready to start?"
    assert all_deps_satisfied(graph[c.repo.url], graph, [a, c]) is True

    # Validate behavior with empty dependency lists
    assert all_deps_satisfied([], graph, [a, c]) is True
    assert all_deps_satisfied(graph[a.repo.url], graph, [a, c]) is True

    # Validate the negative case
    a.status = Release.STATUS.failed
    assert all_deps_satisfied(graph[c.repo.url], graph, [a, c]) is False


@pytest.mark.django_db
@unittest.mock.patch("metaci.release.tasks.get_dependency_graph")
def test_create_dependency_tree(get_dependency_graph):
    graph = defaultdict(list)
    graph["foo"].append("bar")
    get_dependency_graph.return_value = graph
    rc = ReleaseCohortFactory()

    create_dependency_tree(rc)
    assert rc.dependency_graph == {"foo": ["bar"]}


@pytest.mark.django_db
@unittest.mock.patch("metaci.release.tasks.get_dependency_graph")
def test_create_dependency_tree__failure(get_dependency_graph):
    get_dependency_graph.side_effect = DependencyGraphError("foo")
    rc = ReleaseCohortFactory()

    create_dependency_tree(rc)
    assert rc.error_message == str(DependencyGraphError("foo"))
    assert rc.status == ReleaseCohort.STATUS.failed


@pytest.mark.django_db
@unittest.mock.patch("metaci.release.tasks._run_release_builds")
@unittest.mock.patch("metaci.release.tasks.set_merge_freeze_status")
def test_advance_releases(set_merge_freeze_status, run_release_builds):
    graph = defaultdict(list)
    graph["spam"].append("foo")
    graph["baz"].append("bar")
    rc = ReleaseCohortFactory(dependency_graph=graph)
    _ = ReleaseFactory(
        repo__url="foo", release_cohort=rc, status=Release.STATUS.completed
    )
    r2 = ReleaseFactory(
        repo__url="bar", release_cohort=rc, status=Release.STATUS.inprogress
    )
    r3 = ReleaseFactory(
        repo__url="spam", release_cohort=rc, status=Release.STATUS.blocked
    )
    _ = ReleaseFactory(
        repo__url="baz", release_cohort=rc, status=Release.STATUS.blocked
    )

    advance_releases(rc)

    run_release_builds.assert_has_calls([call(r2), call(r3)], any_order=True)


@pytest.mark.django_db
@unittest.mock.patch("metaci.release.tasks.get_dependency_graph")
@unittest.mock.patch("metaci.release.tasks.set_merge_freeze_status")
def test_execute_active_release_cohorts__creates_dependency_trees(
    smfs_mock,
    get_dependency_graph_mock,
):
    rc = ReleaseCohortFactory(status=ReleaseCohort.STATUS.approved)
    _ = ReleaseFactory(
        repo__url="foo", release_cohort=rc, status=Release.STATUS.waiting
    )
    get_dependency_graph_mock.return_value = {}

    execute_active_release_cohorts()
    rc.refresh_from_db()

    assert rc.dependency_graph == {}


@pytest.mark.django_db
@unittest.mock.patch("metaci.release.tasks.set_merge_freeze_status")
@unittest.mock.patch("metaci.release.tasks.advance_releases")
def test_execute_active_release_cohorts__completes_finished_cohorts(
    advance_releases_mock, smfs_mock
):
    rc = ReleaseCohortFactory(status=ReleaseCohort.STATUS.active, dependency_graph={})
    _ = ReleaseFactory(
        repo__url="foo", release_cohort=rc, status=Release.STATUS.completed
    )

    rc_progress = ReleaseCohortFactory(
        status=ReleaseCohort.STATUS.active, dependency_graph={}
    )
    _ = ReleaseFactory(
        repo__url="bar", release_cohort=rc_progress, status=Release.STATUS.blocked
    )
    _ = ReleaseFactory(
        repo__url="baz", release_cohort=rc_progress, status=Release.STATUS.completed
    )

    execute_active_release_cohorts()
    rc.refresh_from_db()
    rc_progress.refresh_from_db()

    assert rc.status == ReleaseCohort.STATUS.completed
    assert rc_progress.status == ReleaseCohort.STATUS.active


@pytest.mark.django_db
@unittest.mock.patch("metaci.release.tasks.advance_releases")
@unittest.mock.patch("metaci.release.tasks.set_merge_freeze_status")
def test_execute_active_release_cohorts__advances_release_cohorts(
    smfs_mock,
    advance_releases_mock,
):
    rc = ReleaseCohortFactory(status=ReleaseCohort.STATUS.active, dependency_graph={})
    _ = ReleaseFactory(
        repo__url="foo", release_cohort=rc, status=Release.STATUS.inprogress
    )
    _ = ReleaseCohortFactory(status=ReleaseCohort.STATUS.completed, dependency_graph={})

    execute_active_release_cohorts()

    advance_releases_mock.assert_called_once_with(rc)


@pytest.mark.django_db
@unittest.mock.patch("metaci.release.tasks.set_merge_freeze_status")
def test_get_dependency_graph(smfs_mock):
    # Create a simulated repo graph that includes:
    # Two repos depending on the same base, one of which also requires the other.
    # A repo with no other relationships

    # Create database entries
    rc = ReleaseCohortFactory(status=ReleaseCohort.STATUS.active, dependency_graph={})
    top = ReleaseFactory(
        repo__url="https://github.com/example/top",
        release_cohort=rc,
        status=Release.STATUS.draft,
        created_from_commit="abc",
    )
    left = ReleaseFactory(
        repo__url="https://github.com/example/left",
        release_cohort=rc,
        status=Release.STATUS.draft,
        created_from_commit="ghi",
    )
    right = ReleaseFactory(
        repo__url="https://github.com/example/right",
        release_cohort=rc,
        status=Release.STATUS.draft,
        created_from_commit="jkl",
    )
    separate = ReleaseFactory(
        repo__url="https://github.com/example/separate",
        release_cohort=rc,
        status=Release.STATUS.draft,
        created_from_commit="mno",
    )

    # Mock results from GitHubDynamicDependency.flatten()
    flatten_results = {
        top.repo.url: [
            UnmanagedGitHubRefDependency(
                github=top.repo.url,
                ref=top.created_from_commit,
                subfolder="unpackaged/pre/first",
            ),
        ],
        left.repo.url: [GitHubDynamicDependency(github=top.repo.url)],
        right.repo.url: [
            GitHubDynamicDependency(github=top.repo.url),
            GitHubDynamicDependency(github=left.repo.url),
        ],
        separate.repo.url: [],
    }

    def flatten_mock(self, context):
        return flatten_results[self.github]

    expected_result = defaultdict(
        list,
        {
            left.repo.url: [top.repo.url],
            right.repo.url: [top.repo.url, left.repo.url],
        },
    )

    with unittest.mock.patch.object(GitHubDynamicDependency, "flatten", flatten_mock):
        assert (
            get_dependency_graph([top, left, right, separate])
            == get_dependency_graph([left, right, separate])
            == expected_result
        )


@pytest.mark.django_db
@unittest.mock.patch("metaci.release.tasks.set_merge_freeze_status")
def test_get_dependency_graph__duplicate_releases(smfs_mock):
    rc = ReleaseCohortFactory(status=ReleaseCohort.STATUS.active, dependency_graph={})
    first = ReleaseFactory(
        repo__url="https://github.com/example/test1",
        release_cohort=rc,
        status=Release.STATUS.draft,
        created_from_commit="abc",
    )
    second = ReleaseFactory(
        repo__url="https://github.com/example/test1",
        release_cohort=rc,
        status=Release.STATUS.draft,
        created_from_commit="ghi",
    )

    with pytest.raises(DependencyGraphError):
        get_dependency_graph([first, second])


@unittest.mock.patch("metaci.release.tasks.get_github_api_for_repo")
def test_non_project_config(get_github_api_mock):
    pc = NonProjectConfig()

    assert (
        pc.get_repo_from_url("https://github.com/test/foo")
        == get_github_api_mock.return_value.repository.return_value
    )
    get_github_api_mock.return_value.repository.assert_called_once_with("test", "foo")
    assert pc.logger is not None
