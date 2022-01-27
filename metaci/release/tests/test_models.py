import datetime
import unittest

import pytest
from django.core.exceptions import ValidationError
from model_utils import Choices

from metaci.conftest import RepositoryFactory
from metaci.fixtures.factories import (
    PlanFactory,
    ReleaseFactory,
    PlanRepositoryFactory,
    ReleaseCohortFactory,
)
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
    @unittest.mock.patch("metaci.release.tasks.set_merge_freeze_status")
    def test_release_cannot_link_to_cohort_unless_status_is_planned(self, smfs_mock):
        cohort = ReleaseCohortFactory()
        cohort.status = "Canceled"
        cohort.save()

        release = ReleaseFactory()
        release.release_cohort=cohort
        with pytest.raises(ValidationError) as e:
            release.save()

        assert "in Planned status" in str(e)

        cohort.status = "Planned"
        cohort.save()
        release.release_cohort=cohort
        release.save()

    @unittest.mock.patch("metaci.release.tasks.set_merge_freeze_status")
    def test_release_cannot_remove_from_cohort_unless_status_is_planned(self, smfs_mock):
        cohort = ReleaseCohortFactory()
        cohort.status = "Planned"
        cohort.save()

        release = ReleaseFactory()
        release.release_cohort=cohort
        release.save()

        cohort.status = "Canceled"
        cohort.save()
        release.release_cohort=None

        with pytest.raises(ValidationError) as e:
            release.save()

        assert "cannot be removed from a Release Cohort" in str(e)

        cohort.status = "Planned"
        cohort.save()
        release.release_cohort=None
        release.save()

    @unittest.mock.patch("metaci.release.tasks.set_merge_freeze_status")
    def test_release_cannot_move_between_cohorts_unless_both_planned(self, smfs_mock):
        cohort = ReleaseCohortFactory(status="Planned")
        other_cohort = ReleaseCohortFactory(status="Canceled")

        release = ReleaseFactory()
        release.release_cohort=cohort
        release.save()

        with pytest.raises(ValidationError) as e:
            release.release_cohort = other_cohort
            release.save()

        assert "Release Cohort in Planned status" in str(e)

    @unittest.mock.patch("metaci.release.tasks.set_merge_freeze_status")
    def test_release_can_move_between_cohorts_both_planned(self, smfs_mock):
        cohort = ReleaseCohortFactory(status="Planned")
        other_cohort = ReleaseCohortFactory(status="Planned")

        release = ReleaseFactory()
        release.release_cohort=cohort
        release.save()

        release.release_cohort = other_cohort
        release.save()  # "assertion" is that no ValidationError is thrown.


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


@pytest.mark.django_db
class TestReleaseCohort:
    def test_validation_active(self):
        cohort = ReleaseCohortFactory()
        with pytest.raises(ValidationError) as e:
            cohort.status = "Completed"
            cohort.clean()
            assert "must be in Active status" in str(e)

    def test_validation_date_without_completed(self):
        cohort = ReleaseCohortFactory()
        with pytest.raises(ValidationError) as e:
            cohort.merge_freeze_start = datetime.datetime.now(
                tz=datetime.timezone.utc
            ) - datetime.timedelta(days=8)
            cohort.merge_freeze_end = datetime.datetime.now(
                tz=datetime.timezone.utc
            ) - datetime.timedelta(days=7)
            cohort.clean()
            assert "must be in Completed or Canceled status" in str(e)

    def test_validation_completed_without_date(self):
        cohort = ReleaseCohortFactory()
        with pytest.raises(ValidationError) as e:
            cohort.status = "Completed"
            cohort.clean()
            assert "may not be in Completed status" in str(e)
