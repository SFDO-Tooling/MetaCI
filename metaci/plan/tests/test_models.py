from django.contrib.auth.models import User
from django.test import TestCase

from metaci.repository.models import Repository
from metaci.plan.models import Plan
from metaci.plan.models import PlanRepository


class PlanTestCase(TestCase):
    def setUp(self):
        self.repo = Repository(
            name="TestRepo",
            owner="TestOwner",
            url="https://github.com/TestOwner/TestRepo",
        )
        self.commit_plan = Plan(
            name="Test Plan",
            role="feature",
            trigger="commit",
            regex="test/.*",
            flows="test_flow",
            org="test_org",
            context="test case",
        )
        self.tag_plan = Plan(
            name="Test Plan",
            role="feature",
            trigger="tag",
            regex="test/.*",
            flows="test_flow",
            org="test_org",
            context="test case",
        )

    def test_check_push_commit_matches(self):
        push = {"ref": "refs/heads/test/matches", "after": "0123456789"}
        run_build, commit, commit_message = self.commit_plan.check_push(push)
        self.assertTrue(run_build)
        self.assertEquals(commit, push["after"])

    def test_check_push_commit_does_not_match(self):
        push = {"ref": "refs/heads/no-match"}
        run_build, commit, commit_message = self.commit_plan.check_push(push)
        self.assertFalse(run_build)
        self.assertEquals(commit, None)

    def test_check_push_commit_tag_event(self):
        push = {"ref": "refs/tags/test/matches", "head_commit": None}
        run_build, commit, commit_message = self.commit_plan.check_push(push)
        self.assertFalse(run_build)
        self.assertEquals(commit, None)

    def test_check_push_tag_matches(self):
        push = {
            "ref": "refs/tags/test/matches",
            "before": "0123456789",
            "head_commit": None,
        }
        run_build, commit, commit_message = self.tag_plan.check_push(push)
        self.assertTrue(run_build)
        self.assertEquals(commit, push["before"])

    def test_check_push_tag_does_not_match(self):
        push = {"ref": "refs/tags/no-match", "head_commit": None}
        run_build, commit, commit_message = self.tag_plan.check_push(push)
        self.assertFalse(run_build)
        self.assertEquals(commit, None)

    def test_check_push_tag_commit_event(self):
        push = {"ref": "refs/heads/test/matches", "head_commit": None}
        run_build, commit, commit_message = self.tag_plan.check_push(push)
        self.assertFalse(run_build)
        self.assertEquals(commit, None)
