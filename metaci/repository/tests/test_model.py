from unittest import mock

import github3.exceptions
import pytest

from metaci.fixtures.factories import BranchFactory, RepositoryFactory


@pytest.mark.django_db
def test_branch_is_tag():
    branch = BranchFactory()
    assert not branch.is_tag()

    branch.name = "tag: " + branch.name
    assert branch.is_tag()


@pytest.mark.django_db
def test_no_repo_latest_release():
    repo = RepositoryFactory()
    assert not repo.latest_release


@pytest.mark.django_db
def test_branch_get_github_api__exception():
    branch = BranchFactory()
    mock_gh = mock.Mock()
    branch.repo.get_github_api = mock_gh

    def raise_error(*args, **kwargs):
        raise github3.exceptions.NotFoundError(mock.Mock())

    mock_gh.return_value.branch = raise_error

    assert branch.get_github_api() is None


@pytest.mark.django_db
def test_branch_get_github_api__normal():
    branch = BranchFactory()
    mock_gh = mock.Mock()
    mock_gh.return_value.branch.return_value = mock_branch_api = object()
    branch.repo.get_github_api = mock_gh
    assert branch.get_github_api() is mock_branch_api
