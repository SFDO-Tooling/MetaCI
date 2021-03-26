# Lots of work to be done here!!!!
import json
from unittest import mock

import responses
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


@mock.patch("metaci.build.tasks.reset_database_connection", lambda: ...)
@mock.patch(
    "metaci.build.management.commands.run_build.scratch_org_limits", lambda: 100
)
class TestLongRunningBuild(TestCase):
    @mock.patch("metaci.build.tasks.lock_org")
    @mock.patch("subprocess.Popen")
    def test_long_running__local(self, popen, lock_org):
        repo = RepositoryFactory(name="myrepo")
        org = OrgFactory(name="myorg", repo=repo, scratch=False)
        plan = PlanFactory(name="myplan", org="myorg", queue="long-running")
        PlanRepositoryFactory(repo=repo, plan=plan)
        build = BuildFactory(repo=repo, plan=plan, org=org)

        def fake_lock_org(*args):
            fake_lock_org.was_called = True
            return True

        fake_lock_org.was_called = False
        lock_org.side_effect = fake_lock_org

        def mock_popen(args):
            assert args[0:4] == [
                "python",
                "./manage.py",
                "run_build_from_id",
                str(build.id),
            ]
            assert args[4].startswith("metaci-org-lock-")
            return mock.MagicMock(pid=5)

        popen.side_effect = mock_popen

        check_queued_build(build.id)

        assert popen.mock_calls
        assert fake_lock_org.was_called

    @mock.patch(
        "metaci.build.models.settings.METACI_LONG_RUNNING_BUILD_CONFIG",
        {"app_name": "test-app"},
    )
    @mock.patch(
        "metaci.build.models.settings.METACI_LONG_RUNNING_BUILD_CLASS",
        "metaci.build.autoscaling.HerokuOneOffBuilder",
    )
    @mock.patch("metaci.build.tasks.lock_org")
    @responses.activate
    def test_long_running__heroku(self, lock_org):
        repo = RepositoryFactory(name="myrepo")
        org = OrgFactory(name="myorg", repo=repo, scratch=False)
        plan = PlanFactory(name="myplan", org="myorg", queue="long-running")
        PlanRepositoryFactory(repo=repo, plan=plan)
        build = BuildFactory(repo=repo, plan=plan, org=org)

        def fake_lock_org(*args):
            fake_lock_org.was_called = True
            return True

        fake_lock_org.was_called = False
        lock_org.side_effect = fake_lock_org

        def matcher(post):
            data = json.loads(post)

            assert data == {
                "command": f"python ./manage.py run_build_from_id {build.id} metaci-org-lock-{org.id}",
                "time_to_live": "86400",
            }

            return True

        responses.add(
            "POST",
            "https://api.heroku.com/apps/test-app/dynos",
            status=200,
            match=[matcher],
            json={"id": "23"},
        )

        check_queued_build(build.id)

        assert fake_lock_org.was_called
