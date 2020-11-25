from unittest import mock

import pytest

from metaci.build.exceptions import BuildError
from metaci.conftest import BuildFactory
from metaci.repository import utils


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

    with mock.patch("metaci.build.models.settings.SITE_URL", "initech.co"):
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

    with mock.patch("metaci.build.models.settings.SITE_URL", "initech.co"):
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

    with mock.patch("metaci.build.models.settings.SITE_URL", "initech.co"):
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

    with mock.patch("metaci.build.models.settings.SITE_URL", "initech.co"):
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

    with mock.patch("metaci.build.models.settings.SITE_URL", "initech.co"):
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
    with mock.patch("metaci.build.models.settings.SITE_URL", "initech.co"):
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
    with mock.patch("metaci.build.models.settings.SITE_URL", "initech.co"):
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
    with mock.patch("metaci.build.models.settings.SITE_URL", "initech.co"):
        utils.create_status(build)
        repo.create_status.assert_called_once_with(
            sha=build.commit,
            state="error",
            target_url=f"initech.co/builds/{build.id}",
            description="💥  An error occurred during the build",
            context=build.plan.context,
        )


@pytest.mark.django_db
def test_create_status__fail():
    build, repo = setup_build_with_status("fail")
    build.tests_fail = 2
    with mock.patch("metaci.build.models.settings.SITE_URL", "initech.co"):
        utils.create_status(build)
        repo.create_status.assert_called_once_with(
            sha=build.commit,
            state="failure",
            target_url=f"initech.co/builds/{build.id}/tests",
            description="⚠ ️There were 2 tests that failed.",
            context=build.plan.context,
        )


@pytest.mark.django_db
def test_create_status__fail_singular():
    build, repo = setup_build_with_status("fail")
    build.tests_fail = 1
    with mock.patch("metaci.build.models.settings.SITE_URL", "initech.co"):
        utils.create_status(build)
        repo.create_status.assert_called_once_with(
            sha=build.commit,
            state="failure",
            target_url=f"initech.co/builds/{build.id}/tests",
            description="⚠ ️There was 1 test that failed.",
            context=build.plan.context,
        )


@pytest.mark.django_db
def test_create_status__fail_qa():
    build, repo = setup_build_with_status("fail")
    build.plan.role = "qa"
    with mock.patch("metaci.build.models.settings.SITE_URL", "initech.co"):
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
