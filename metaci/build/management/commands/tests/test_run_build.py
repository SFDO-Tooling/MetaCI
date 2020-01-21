import os
from unittest import mock

import pytest
from django.conf import settings
from django.test import TestCase

from metaci.build.management.commands.run_build import Command
from metaci.build.models import Build
from metaci.conftest import (
    BranchFactory,
    OrgFactory,
    PlanFactory,
    PlanRepositoryFactory,
    RepositoryFactory,
    UserFactory,
)

BUILD_TIMEOUT = 100


@mock.patch("metaci.build.management.commands.run_build.scratch_org_limits")
@mock.patch("metaci.build.management.commands.run_build.run_build")
@pytest.mark.django_db
class TestRunBuild(TestCase):
    def test_run_build_persistent(self, run_build, scratch_org_limits):
        self._testrun_build(run_build, scratch_org_limits, False)

    def test_run_build_scratch(self, run_build, scratch_org_limits):
        self._testrun_build(run_build, scratch_org_limits, True)

    def _testrun_build(self, run_build, scratch_org_limits, org_is_scratch):
        repo = RepositoryFactory(name="myrepo")
        branch = BranchFactory(name="mybranch", repo=repo)
        plan = PlanFactory(name="myplan", org="myorg", build_timeout=BUILD_TIMEOUT)
        PlanRepositoryFactory(repo=repo, plan=plan)
        user = UserFactory(username="username")
        org = OrgFactory(name="myorg", repo=repo, scratch=org_is_scratch)
        os.environ["DYNO"] = "worker.42"
        build_pk = None

        def side_effect(build_id):
            nonlocal build_pk
            build_pk = build_id

        run_build.side_effect = side_effect
        scratch_org_limits.return_value = mock.Mock()
        scratch_org_limits.return_value.remaining = settings.SCRATCH_ORG_RESERVE + 5
        c = Command()
        c.handle("myrepo", "mybranch", "commit", "myplan", "username")
        assert build_pk
        build = Build.objects.get(pk=build_pk)
        assert not build.task_id_check  # wasn't queued
        assert build.build_type == "manual-command"
        assert build.user == user
        assert build.repo == repo
        assert build.branch == branch
        assert build.plan == plan
        assert build.org == org

    @mock.patch("metaci.build.management.commands.run_build.lock_org")
    def test_run_build_sets_lock(self, lock_org, run_build, scratch_org_limits):
        self._testrun_build(run_build, scratch_org_limits, False)
        assert lock_org.mock_calls[0][1][2] == 100
