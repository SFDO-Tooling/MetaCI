import pytest
from django.core.exceptions import ValidationError
from django.test import TestCase

from metaci.plan.models import Plan
from metaci.repository.models import Repository


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

    def test_check_github_event__commit_matches(self):
        payload = {"ref": "refs/heads/test/matches", "after": "0123456789"}
        run_build, commit, commit_message = self.commit_plan.check_github_event(
            "push", payload
        )
        self.assertTrue(run_build)
        self.assertEqual(commit, payload["after"])

    def test_check_github_event__commit_does_not_match(self):
        payload = {"ref": "refs/heads/no-match"}
        run_build, commit, commit_message = self.commit_plan.check_github_event(
            "push", payload
        )
        self.assertFalse(run_build)
        self.assertEqual(commit, None)

    def test_check_github_event__commit_tag_event(self):
        payload = {"ref": "refs/tags/test/matches", "head_commit": None}
        run_build, commit, commit_message = self.commit_plan.check_github_event(
            "push", payload
        )
        self.assertFalse(run_build)
        self.assertEqual(commit, None)

    def test_check_github_event__tag_matches(self):
        payload = {"ref": "refs/tags/test/matches", "head_commit": {"id": "0123456789"}}
        run_build, commit, commit_message = self.tag_plan.check_github_event(
            "push", payload
        )
        self.assertTrue(run_build)
        self.assertEqual(commit, payload["head_commit"]["id"])

    def test_check_github_event__tag_does_not_match(self):
        payload = {"ref": "refs/tags/no-match", "head_commit": None}
        run_build, commit, commit_message = self.tag_plan.check_github_event(
            "push", payload
        )
        self.assertFalse(run_build)
        self.assertEqual(commit, None)

    def test_check_github_event__tag_commit_event(self):
        payload = {"ref": "refs/heads/test/matches", "head_commit": None}
        run_build, commit, commit_message = self.tag_plan.check_github_event(
            "push", payload
        )
        self.assertFalse(run_build)
        self.assertEqual(commit, None)

    def test_check_github_event__status_event(self):
        payload = {"context": "Package Upload", "state": "success", "sha": "SHA"}
        plan = Plan(
            name="Test Plan",
            role="feature",
            trigger="status",
            commit_status_regex="Package Upload",
            flows="test_flow",
            org="test_org",
            context="test case",
        )
        run_build, commit, commit_message = plan.check_github_event("status", payload)
        assert run_build
        assert commit == "SHA"

    def test_check_github_event__status_event_negative(self):
        payload = {"context": "Package Upload", "state": "success", "sha": "SHA"}
        plan = Plan(
            name="Test Plan",
            role="feature",
            trigger="status",
            commit_status_regex="Commit Status",
            flows="test_flow",
            org="test_org",
            context="test case",
        )
        run_build, commit, commit_message = plan.check_github_event("status", payload)
        assert not run_build

    def test_check_github_event__status_event_with_branch_regex(self):
        payload = {
            "context": "Package Upload",
            "state": "success",
            "sha": "SHA",
            "branches": [
                {
                    "name": "test/somefeature",
                    "commit": {
                        "sha": "SHA",
                        "url": "https://api.github.com/repos/Test/Test/commits/SHA",
                    },
                    "protected": False,
                }
            ],
        }
        plan = Plan(
            name="Test Plan",
            role="feature",
            trigger="status",
            regex="test/",
            commit_status_regex="Package Upload",
            flows="test_flow",
            org="test_org",
            context="test case",
        )
        run_build, commit, commit_message = plan.check_github_event("status", payload)
        assert run_build
        assert commit == "SHA"

    def test_check_github_event__status_event_with_branch_regex_negative(self):
        payload = {
            "context": "Package Upload",
            "state": "success",
            "sha": "SHA",
            "branches": [
                {
                    "name": "test/somefeature",
                    "commit": {
                        "sha": "SHA",
                        "url": "https://api.github.com/repos/Test/Test/commits/SHA",
                    },
                    "protected": False,
                }
            ],
        }
        plan = Plan(
            name="Test Plan",
            role="feature",
            trigger="status",
            regex="feature/",
            commit_status_regex="Package Upload",
            flows="test_flow",
            org="test_org",
            context="test case",
        )
        run_build, commit, commit_message = plan.check_github_event("status", payload)
        assert not run_build

    def test_plan_saved_without_regex(self):
        self.commit_plan.regex = None
        with pytest.raises(
            ValidationError,
            match="Plans with a trigger type other than Manual or Commit Status must also specify a regex to match tags or branches.",
        ):
            self.commit_plan.clean()

    def test_commit_plan_saved_without_regex(self):
        self.commit_plan.commit_status_regex = None
        self.commit_plan.trigger = "status"
        with pytest.raises(
            ValidationError,
            match="Plans with a Commit Status trigger must specify a Commit Status Regex.",
        ):
            self.commit_plan.clean()

    def test_non_commit_status_plan_saved_with_status_regex(self):
        self.commit_plan.commit_status_regex = "foo"
        self.commit_plan.trigger = "manual"
        with pytest.raises(
            ValidationError,
            match="Only Plans with a Commit Status trigger may specify a Commit Status Regex.",
        ):
            self.commit_plan.clean()
