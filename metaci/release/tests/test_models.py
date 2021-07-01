import datetime

import pytest
from model_utils import Choices

from metaci.conftest import RepositoryFactory
from metaci.fixtures.factories import PlanFactory, PlanRepositoryFactory
from metaci.release.models import (
    ChangeCaseTemplate,
    DefaultImplementationStep,
    ImplementationStep,
    Release,
)
from metaci.repository.models import Repository


@pytest.mark.django_db
class TestChangeCaseTemplate:
    def test_change_case_template_str(self):
        assert str(ChangeCaseTemplate(name="test")) == "test"


@pytest.mark.django_db
class TestImplementationSteps:
    def test_change_case_template_str(self):
        assert str(ImplementationStep(plan=PlanFactory(name="test"))) == "test"


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

    def test_release_implementation_steps_plan_role(self):
        plan = PlanFactory(role="release", change_traffic_control=True)
        plan.save()
        repo = RepositoryFactory(
            default_implementation_steps=[
                {
                    "role": "release",
                    "duration": 10,
                    "start_time": 8,
                    "start_date_offset": 0,
                },
            ],
        )
        repo.save()
        planrepo = PlanRepositoryFactory(plan=plan, repo=repo)
        planrepo.save()
        change_case_template = ChangeCaseTemplate()
        change_case_template.save()
        release = Release(
            repo=repo,
            change_case_template=change_case_template,
        )
        release.save()
        assert release.implementation_steps.count() == 1

    def test_release_implementation_steps_no_plan_role(self):
        release_step = {
            "role": "release",
            "duration": 10,
            "start_time": 8,
            "start_date_offset": 0,
        }
        wrong_step = {
            "role": "ale",
            "duration": 10,
            "start_time": 8,
            "start_date_offset": 0,
        }
        release = Release(
            repo=RepositoryFactory(default_implementation_steps=[release_step]),
            change_case_template=ChangeCaseTemplate(),
        )
        default_step = DefaultImplementationStep(**wrong_step)
        assert release.create_default_implementation_step(default_step) is None
