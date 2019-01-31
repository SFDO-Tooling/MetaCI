from unittest import mock
from django.test import TestCase

from metaci.build.signals import build_complete
from metaci.repository.models import Branch, Repository
from metaci.plan.models import Plan, PlanRepository, PlanRepositoryTrigger
from metaci.build.models import Build


class PlanHandlerTestCase(TestCase):
    def setUp(self):
        self.repo = Repository.objects.create(
            name="TestRepo",
            owner="TestOwner",
            github_id="0",
            url="https://github.com/TestOwner/TestRepo",
        )
        self.triggered_repo = Repository.objects.create(
            name="TriggeredRepo",
            owner="TestOwner",
            github_id="1",
            url="https://github.com/TestOwner/TriggeredRepo",
        )
        self.plan = Plan.objects.create(
            name="Test Plan",
            role="feature",
            trigger="commit",
            regex="test/.*",
            flows="test_flow",
            org="test_org",
            context="test case",
        )
        self.plan_repo = PlanRepository.objects.create(plan=self.plan, repo=self.repo)
        self.branch = Branch.objects.create(repo=self.triggered_repo, name="master")
        self.plan_repo_trigger = PlanRepositoryTrigger.objects.create(
            plan_repo=self.plan_repo, repo=self.repo, branch="master"
        )
        self.build = Build.objects.create(
            repo=self.triggered_repo, planrepo=self.plan_repo, plan=self.plan
        )

    def test_should_send_on_build_success(self):
        with mock.patch(
            "metaci.plan.handlers.trigger_dependent_builds", autospec=True
        ) as handler:
            build_complete.connect(handler, sender="sender")
            build_complete.send(sender="sender", build=self.build, status="success")
            handler.assert_called_once()

    def test_build_triggered(self):
        self.plan_repo_trigger.fire(self.build)
        enqueued_build = Build.objects.get(repo=self.triggered_repo)
        self.assertIsNotNone(enqueued_build)
        self.assertIsNotNone(enqueued_build.task_id_check)  # build has been queued
