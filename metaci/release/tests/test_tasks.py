from metaci.fixtures.factories import ChangeCaseTemplateFactory
from metaci.repository.models import Repository
from metaci.release.models import ChangeCaseTemplate, Release
import pytest
from unittest import mock


@pytest.mark.django_db
@mock.patch("metaci.release.tasks.datetime.now")
def test_get_scope_changes(now_mock):
    now_mock.return_value = ()  # TODO

    release = Release(
        repo=Repository(), change_case_template=ChangeCaseTemplateFactory()
    )
