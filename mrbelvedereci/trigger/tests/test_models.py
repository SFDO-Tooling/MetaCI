from django.contrib.auth.models import User
from django.test import TestCase

from mrbelvedereci.github.models import Repository
from mrbelvedereci.trigger.models import Trigger


class TriggerTestCase(TestCase):

    def setUp(self):
        self.repo = Repository(
            name = 'TestRepo',
            owner = 'TestOwner',
            url = 'https://github.com/TestOwner/TestRepo'
        )
        self.commit_trigger = Trigger(
            name = 'Test Trigger',
            repo = self.repo, 
            type = 'commit',
            regex = 'test/.*',
            flows = 'test_flow',
            org = 'test_org',
            context = 'test case'
        )
        self.tag_trigger = Trigger(
            name = 'Test Trigger',
            repo = self.repo, 
            type = 'tag',
            regex = 'test/.*',
            flows = 'test_flow',
            org = 'test_org',
            context = 'test case'
        )

    def test_check_push_commit_matches(self):
        push = {
            'ref': 'refs/heads/test/matches',
        }
        self.assertTrue(self.commit_trigger.check_push(push))

    def test_check_push_commit_does_not_match(self):
        push = {
            'ref': 'refs/heads/no-match',
        }
        self.assertFalse(self.commit_trigger.check_push(push))

    def test_check_push_commit_tag_event(self):
        push = {
            'ref': 'refs/tags/test/matches',
        }
        self.assertFalse(self.commit_trigger.check_push(push))

    def test_check_push_tag_matches(self):
        push = {
            'ref': 'refs/tags/test/matches',
        }
        self.assertTrue(self.tag_trigger.check_push(push))

    def test_check_push_tag_does_not_match(self):
        push = {
            'ref': 'refs/tags/no-match',
        }
        self.assertFalse(self.tag_trigger.check_push(push))

    def test_check_push_tag_commit_event(self):
        push = {
            'ref': 'refs/heads/test/matches',
        }
        self.assertFalse(self.tag_trigger.check_push(push))

