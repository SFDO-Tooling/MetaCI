from unittest import mock

import pytest

from metaci.build.exceptions import BuildError
from metaci.conftest import BuildFactory, BuildFlowFactory
from metaci.repository import utils


@pytest.fixture(scope="module", autouse=True)
def site_url():
    with mock.patch("metaci.build.models.settings.SITE_URL", "initech.co"):
        yield


def setup_build_with_status(status):
    """Sets items that need to be mocked"""
    build = BuildFactory(status=status)
    assert build.get_status() == status

    # needed for metaci.repository.utils.create_status()
    repo = mock.Mock()
    repo.create_status = mock.Mock()
    build.plan.context = mock.Mock()
    build.repo.get_github_api = mock.Mock(return_value=repo)
    return build, repo


@pytest.mark.django_db
def test_create_status__queued():
    build, repo = setup_build_with_status("queued")

    utils.create_status(build)

    repo.create_status.assert_called_once_with(
        sha=build.commit,
        state="pending",
        target_url=f"initech.co/builds/{build.id}",
        description="The build is queued",
        context=build.plan.context,
    )


@pytest.mark.django_db
def test_create_status__waiting():
    build, repo = setup_build_with_status("waiting")

    utils.create_status(build)
    repo.create_status.assert_called_once_with(
        sha=build.commit,
        state="pending",
        target_url=f"initech.co/builds/{build.id}",
        description="The build is waiting for another build to complete",
        context=build.plan.context,
    )


@pytest.mark.django_db
def test_create_status__running():
    build, repo = setup_build_with_status("running")

    utils.create_status(build)
    repo.create_status.assert_called_once_with(
        sha=build.commit,
        state="pending",
        target_url=f"initech.co/builds/{build.id}",
        description="The build is running",
        context=build.plan.context,
    )


@pytest.mark.django_db
def test_create_status__qa():
    build, repo = setup_build_with_status("qa")

    utils.create_status(build)
    repo.create_status.assert_called_once_with(
        sha=build.commit,
        state="pending",
        target_url=f"initech.co/builds/{build.id}",
        description=f"{build.user} is testing",
        context=build.plan.context,
    )


@pytest.mark.django_db
def test_create_status__success():
    build, repo = setup_build_with_status("success")

    utils.create_status(build)
    repo.create_status.assert_called_once_with(
        sha=build.commit,
        state="success",
        target_url=f"initech.co/builds/{build.id}",
        description="The build was successful",
        context=build.plan.context,
    )


@pytest.mark.django_db
def test_create_status__success_qa():
    build, repo = setup_build_with_status("success")
    build.plan.role = "qa"

    utils.create_status(build)
    repo.create_status.assert_called_once_with(
        sha=build.commit,
        state="success",
        target_url=f"initech.co/builds/{build.id}",
        description=f"{build.qa_user} approved. See details for QA comments",
        context=build.plan.context,
    )


@pytest.mark.django_db
def test_create_status__success_with_commit_status():
    build, repo = setup_build_with_status("success")
    build.commit_status = "This build is malarky"

    utils.create_status(build)
    repo.create_status.assert_called_once_with(
        sha=build.commit,
        state="success",
        target_url=f"initech.co/builds/{build.id}",
        description="This build is malarky",
        context=build.plan.context,
    )


@pytest.mark.django_db
def test_create_status__error():
    build, repo = setup_build_with_status("error")

    utils.create_status(build)
    repo.create_status.assert_called_once_with(
        sha=build.commit,
        state="error",
        target_url=f"initech.co/builds/{build.id}",
        description="An error occurred during the build",
        context=build.plan.context,
    )


@pytest.mark.django_db
def test_create_status__fail():
    build, repo = setup_build_with_status("fail")
    # First BuildFlow
    BuildFlowFactory(build=build)
    # Second BuildFlow, this one has a failing test :(
    bf = BuildFlowFactory(build=build)
    bf.tests_fail = 1
    bf.save()

    utils.create_status(build)
    repo.create_status.assert_called_once_with(
        sha=build.commit,
        state="failure",
        target_url=f"initech.co/builds/{build.id}/tests",
        description="⚠ ️1/2 failed",  # each BuildFlow has total_tests == 1
        context=build.plan.context,
    )


@pytest.mark.django_db
def test_create_status__fail_qa():
    build, repo = setup_build_with_status("fail")
    build.plan.role = "qa"
    utils.create_status(build)
    repo.create_status.assert_called_once_with(
        sha=build.commit,
        state="failure",
        target_url=f"initech.co/builds/{build.id}",
        description=f"{build.qa_user} rejected. See details for QA comments",
        context=build.plan.context,
    )


@pytest.mark.django_db
def test_create_status__unrecognized_status():
    build, repo = setup_build_with_status("this-is-odd")
    with pytest.raises(BuildError):
        utils.create_status(build)
