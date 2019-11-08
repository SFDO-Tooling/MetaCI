import pytest
from unittest import mock
from django.test import TestCase

from metaci.repository import views


class TestGithubPushWebHook(TestCase):
    def test_get_or_create_release(self):

        assert release

    @mock.patch("metaci.repository.views.re.match")
    def test_tag_is_release(self, match):
        repo = mock.Mock()
        repo.release_tag_regex = "some-regex"
        tag = "sample-tag-name"

        match.return_value = True
        views.tag_is_release(tag, repo)
        match.assert_called_once_with("some-regex", tag)

        views.tag_is_release(tag, repo)
        assert match.call_count == 2

    def test_get_tag_name_from_ref(self):
        tagged_release = "beta/1.7-Beta_1749"
        tag_prefix = views.TAG_BRANCH_PREFIX
        test_ref = f"{tag_prefix}{tagged_release}"

        tag_name = views.get_tag_name_from_ref(test_ref)
        assert tag_name == tagged_release

