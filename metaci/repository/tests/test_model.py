import pytest

from metaci.fixtures.factories import BranchFactory


@pytest.mark.django_db
def test_branch_is_tag():
    branch = BranchFactory()
    assert not branch.is_tag()

    branch.name = "tag: " + branch.name
    assert branch.is_tag()
