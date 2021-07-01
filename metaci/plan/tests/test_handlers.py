from unittest import mock

import github3
import pytest
from django.core.exceptions import ObjectDoesNotExist
from django.test import TestCase

from metaci.build.models import Build
from metaci.build.signals import build_complete
from metaci.plan.models import Plan, PlanRepository, PlanRepositoryTrigger
from metaci.repository.models import Branch, Repository


class PlanHandlerTestCase(TestCase):
    def setUp(self):
        self.source_repo = Repository.objects.create(
            name="TestRepo",
            owner="TestOwner",
            github_id="0",
            url="https://github.com/TestOwner/TestRepo",
        )
        self.target_repo = Repository.objects.create(
            name="TriggeredRepo",
            owner="TestOwner",
            github_id="1",
            url="https://github.com/TestOwner/TriggeredRepo",
        )
        self.source_plan = Plan.objects.create(
            name="Source Plan",
            role="feature",
            trigger="commit",
            regex="test/.*",
            flows="test_flow",
            org="test_org",
            context="test case",
        )
        self.target_plan = Plan.objects.create(
            name="Target Plan",
            role="feature",
            trigger="commit",
            regex="test/.*",
            flows="test_flow",
            org="test_org",
            context="test case",
        )
        self.source_plan_repo = PlanRepository.objects.create(
            plan=self.source_plan, repo=self.source_repo
        )
        self.target_plan_repo = PlanRepository.objects.create(
            plan=self.target_plan, repo=self.target_repo
        )

        self.branch = Branch.objects.create(repo=self.target_repo, name="main")

        self.plan_repo_trigger = PlanRepositoryTrigger.objects.create(
            source_plan_repo=self.source_plan_repo,
            target_plan_repo=self.target_plan_repo,
            branch="main",
        )
        self.build = Build.objects.create(
            repo=self.source_repo,
            planrepo=self.source_plan_repo,
            plan=self.source_plan,
            log="",
        )

    @mock.patch("metaci.plan.models.PlanRepositoryTrigger._get_commit")
    def test_should_send_on_build_success(self, get_commit):
        get_commit.return_value = "f1d2d2f924e986ac86fdf7b36c94bcdf32beec15"
        with mock.patch(
            "metaci.plan.handlers.trigger_dependent_builds", autospec=True
        ) as handler:
            build_complete.connect(handler, sender="sender")
            build_complete.send(sender="sender", build=self.build, status="success")
            handler.assert_called_once()

    @mock.patch("metaci.plan.models.PlanRepositoryTrigger._get_commit")
    def test_build_triggered(self, get_commit):
        get_commit.return_value = "f1d2d2f924e986ac86fdf7b36c94bcdf32beec15"
        self.plan_repo_trigger.fire(self.build)
        enqueued_build = Build.objects.get(repo=self.target_repo)
        self.assertIsNotNone(enqueued_build)
        self.assertIsNotNone(enqueued_build.task_id_check)  # build has been queued

    @mock.patch("metaci.plan.models.PlanRepositoryTrigger._get_commit")
    def test_trigger_errors_are_logged(self, get_commit):
        get_commit.side_effect = github3.exceptions.NotFoundError
        build_complete.send(sender="sender", build=self.build, status="success")
        assert (
            "Could not trigger plan [TestOwner/TriggeredRepo] Target Plan (main branch)"
            in self.build.log
        )
        # confirm trigger was not successful
        with pytest.raises(ObjectDoesNotExist):
            Build.objects.get(repo=self.target_repo)
