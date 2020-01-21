# Lots of work to be done here!!!!

from unittest import mock

from django.test import TestCase

from metaci.build.tasks import check_queued_build
from metaci.conftest import (
    BuildFactory,
    OrgFactory,
    PlanFactory,
    PlanRepositoryFactory,
    RepositoryFactory,
)


@mock.patch("metaci.build.tasks.reset_database_connection")
class TestRunBuild(TestCase):
    @mock.patch("metaci.build.management.commands.run_build.scratch_org_limits")
    @mock.patch("metaci.build.tasks.lock_org")
    @mock.patch("metaci.build.models.Build.run")
    def test_lock_set(
        self, run, lock_org, scratch_org_limits, reset_database_connection
    ):
        build_timeout = 100
        repo = RepositoryFactory(name="myrepo")
        OrgFactory(name="myorg", repo=repo, scratch=False)
        plan = PlanFactory(name="myplan", org="myorg", build_timeout=build_timeout)
        build = BuildFactory(repo=repo, plan=plan)
        PlanRepositoryFactory(repo=repo, plan=plan)
        check_queued_build(build.id)
        print(lock_org.mock_calls)
        assert lock_org.mock_calls
        assert lock_org.mock_calls[0][1][2] == build_timeout
