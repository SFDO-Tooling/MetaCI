import os
from unittest import mock

import pytest
from django.test import TestCase

from metaci.build.management.commands.run_build import Command
from metaci.conftest import (
    BranchFactory,
    OrgFactory,
    PlanFactory,
    PlanRepositoryFactory,
    RepositoryFactory,
    UserFactory,
)


@mock.patch("metaci.build.management.commands.run_build.run_build")
@pytest.mark.django_db
class TestRunBuild(TestCase):
    # def test_run_build_scratch(self, run_build):
    #     self._testrun_build(run_build, True)

    def test_run_build_persistent(self, run_build):
        self._testrun_build(run_build, False)

    def test_run_build_persistent_2(self, run_build):
        self._testrun_build(run_build, False)

    def test_run_build_persistent_3(self, run_build):
        self._testrun_build(run_build, False)

    def _testrun_build(self, run_build, org_is_scratch):
        repo = RepositoryFactory(name="myrepo")
        BranchFactory(name="mybranch", repo=repo)
        plan = PlanFactory(name="myplan", org="myorg")
        PlanRepositoryFactory(repo=repo, plan=plan)
        UserFactory(username="username")
        OrgFactory(name="myorg", repo=repo, scratch=org_is_scratch)
        os.environ["DYNO"] = "worker.42"
        c = Command()
        c.handle("myrepo", "mybranch", "commit", "myplan", "username")
