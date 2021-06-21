import datetime

import pytest
from model_utils import Choices

from metaci.release.models import ChangeCaseTemplate, Release
from metaci.repository.models import Repository


@pytest.mark.django_db
class TestRelease:
    def test_empty_release_init(self):
        release = Release(repo=Repository(), change_case_template=ChangeCaseTemplate())
        assert release.release_creation_date == datetime.date.today()
        assert release.sandbox_push_date == datetime.date.today()
        assert (
            release.production_push_date
            == datetime.date.today() + datetime.timedelta(days=6)
        )

        assert release.STATUS == Choices("draft", "published", "hidden")
        assert release.created
        assert release.modified
        assert not release.version_name  # checking default set to None
        assert not release.version_number  # checking default set to None
        assert not release.package_version_id  # checking default set to None
        assert not release.git_tag  # checking default set to None
        assert not release.trialforce_id  # checking default set to None
        assert not release.created_from_commit  # checking default set to None
        assert not release.work_item_link  # checking default set to None
        assert release.change_case_template  # checking default see not None
        assert not release.change_case_link  # checking default set to None
