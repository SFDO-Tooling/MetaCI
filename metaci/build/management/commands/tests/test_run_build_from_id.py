from unittest import mock

import pytest
from django.test import TestCase

from metaci.build.management.commands.run_build_from_id import Command
from metaci.conftest import (
    BuildFactory,
    OrgFactory,
    PlanFactory,
    PlanRepositoryFactory,
    RepositoryFactory,
)


@pytest.mark.django_db
@mock.patch("metaci.build.tasks.reset_database_connection", lambda: ...)
@mock.patch("metaci.cumulusci.handlers.association_helper")
class TestRunBuild(TestCase):
    @mock.patch("metaci.build.models.Build.run")
    def test_lock_set(self, association_helper_mock, run):
        repo = RepositoryFactory(name="myrepo")
        org = OrgFactory(name="myorg", repo=repo, scratch=False)
        plan = PlanFactory(name="myplan", org="myorg")
        build = BuildFactory(repo=repo, plan=plan, org=org)
        PlanRepositoryFactory(repo=repo, plan=plan)
        c = Command()
        c.handle(build_id=build.id, lock_id="abcde")
        assert run.mock_calls
