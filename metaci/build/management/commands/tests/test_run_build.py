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


@pytest.mark.django_db
class TestRunBuild(TestCase):
    def test_run_build_persistent(self):
        self._testrun_build(org_is_scratch=False, no_lock=False)

    def test_run_build_scratch(self):
        self._testrun_build(org_is_scratch=True, no_lock=False)

    def _testrun_build(self, org_is_scratch, no_lock, queue_name="default"):
        with mock.patch(
            "metaci.build.management.commands.run_build.scratch_org_limits"
        ) as scratch_org_limits, mock.patch(
            "metaci.build.management.commands.run_build.run_build"
        ) as run_build, mock.patch(
            "metaci.build.tasks.reset_database_connection", lambda: ...
        ):
            repo = RepositoryFactory(name="myrepo")
            branch = BranchFactory(name="mybranch", repo=repo)
            plan = PlanFactory(name="myplan", org="myorg", build_timeout=BUILD_TIMEOUT)
            PlanRepositoryFactory(repo=repo, plan=plan)
            user = UserFactory(username="username")
            org = OrgFactory(name="myorg", repo=repo, scratch=org_is_scratch)
            os.environ["DYNO"] = "worker.42"
            built_pk = None

            def fake_run_build(build_id, lock_id):
                nonlocal built_pk
                built_pk = build_id

            run_build.side_effect = fake_run_build
            scratch_org_limits.return_value = mock.Mock()
            scratch_org_limits.return_value.remaining = settings.SCRATCH_ORG_RESERVE + 5
            c = Command()
            c.handle(
                "myrepo",
                "mybranch",
                "commit",
                "myplan",
                "username",
                no_lock=no_lock,
            )
            build = Build.objects.get(pk=built_pk)
            assert not build.task_id_check
            assert build.build_type == "manual-command"
            assert built_pk
            assert build.user == user
            assert build.repo == repo
            assert build.branch == branch
            assert build.plan == plan
            assert build.org == org

    @mock.patch("metaci.build.management.commands.run_build.lock_org")
    def test_run_build_sets_lock(self, lock_org):
        self._testrun_build(org_is_scratch=False, no_lock=False)
        assert lock_org.mock_calls[0][1][2] == 100

    @mock.patch("metaci.build.management.commands.run_build.lock_org")
    def test_run_build_can_skip_lock(self, lock_org):
        self._testrun_build(org_is_scratch=False, no_lock=True)
        assert not lock_org.mock_calls

    def test_run_build_scratch_queued(self):
        self._testrun_build(org_is_scratch=True, no_lock=False)

    def test_run_build_persistent_queued(self):
        self._testrun_build(org_is_scratch=False, no_lock=False)

    def test_run_build_long_running(self):
        self._testrun_build(org_is_scratch=False, no_lock=False)
