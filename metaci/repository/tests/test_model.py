from unittest import mock

import pytest

from metaci.fixtures.factories import BranchFactory


@pytest.mark.django_db
def test_branch_is_tag():
    branch = BranchFactory()
    assert not branch.is_tag()

    branch.name = "tag: " + branch.name
    assert branch.is_tag()


@pytest.mark.django_db
def test_branch_get_github_api():
    branch = BranchFactory()
    assert branch.get_github_api() is None

    mock_gh = mock.Mock()
    mock_gh.return_value.branch.return_value = mock_branch_api = object()
    branch.repo.get_github_api = mock_gh
    assert branch.get_github_api() is mock_branch_api
