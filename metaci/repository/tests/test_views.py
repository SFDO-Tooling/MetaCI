from datetime import datetime, timezone, timedelta
import json
from unittest import mock
from unittest.mock import patch

import pytest
from django.core.exceptions import PermissionDenied
from django.test import Client, TestCase
from django.test.client import RequestFactory
from django.urls import reverse
from guardian.shortcuts import assign_perm

from metaci.build.models import Build
from metaci.conftest import (
    BranchFactory,
    PlanFactory,
    PlanRepositoryFactory,
    ReleaseFactory,
    RepositoryFactory,
    StaffSuperuserFactory,
    UserFactory,
)
from metaci.fixtures.factories import ReleaseCohortFactory
from metaci.release.models import ReleaseCohort
from metaci.repository import views
from metaci.repository.models import Branch


class TestRepositoryViews(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.client = Client()
        cls.superuser = StaffSuperuserFactory()
        cls.user = UserFactory()
        cls.plan = PlanFactory(name="Plan1")
        cls.plan.dashboard = "last"
        cls.plan.trigger = "tag"
        cls.plan.regex = "beta"
        cls.plan.save()
        cls.repo = RepositoryFactory(name="PublicRepo")
        cls.planrepo = PlanRepositoryFactory(plan=cls.plan, repo=cls.repo)
        cls.branch = BranchFactory(name="test-branch", repo=cls.repo)
        super(TestRepositoryViews, cls).setUpTestData()

    @pytest.mark.django_db
    def test_repo_list(self):
        self.client.force_login(self.superuser)
        url = reverse("repo_list")

        response = self.client.get(url)
        assert response.status_code == 200

    @pytest.mark.django_db
    def test_repo_detail__as_superuser(self):
        self.client.force_login(self.superuser)
        url = reverse(
            "repo_detail", kwargs={"owner": self.repo.owner, "name": self.repo.name}
        )

        response = self.client.get(url)
        assert response.status_code == 200

    @pytest.mark.django_db
    def test_repo_detail__as_user(self):
        self.client.force_login(self.user)
        url = reverse(
            "repo_detail", kwargs={"owner": self.repo.owner, "name": self.repo.name}
        )

        response = self.client.get(url)
        assert response.status_code == 404  # no permissions

        assign_perm("plan.view_builds", self.user, self.planrepo)

        response = self.client.get(url)
        assert response.status_code == 200

    @pytest.mark.django_db
    def test_repo_branches__as_superuser(self):
        self.client.force_login(self.superuser)
        url = reverse(
            "repo_branches", kwargs={"owner": self.repo.owner, "name": self.repo.name}
        )

        response = self.client.get(url)
        assert response.status_code == 200

    @pytest.mark.django_db
    def test_repo_branches__as_user(self):
        self.client.force_login(self.user)
        url = reverse(
            "repo_branches", kwargs={"owner": self.repo.owner, "name": self.repo.name}
        )

        response = self.client.get(url)
        assert response.status_code == 404  # no permissions

        assign_perm("plan.view_builds", self.user, self.planrepo)

        response = self.client.get(url)
        assert response.status_code == 200

    @pytest.mark.django_db
    def test_repo_plans__as_superuser(self):
        self.client.force_login(self.superuser)
        url = reverse(
            "repo_plans", kwargs={"owner": self.repo.owner, "name": self.repo.name}
        )

        response = self.client.get(url)
        assert response.status_code == 200

    @pytest.mark.django_db
    def test_repo_plans__as_user(self):
        self.client.force_login(self.user)
        url = reverse(
            "repo_plans", kwargs={"owner": self.repo.owner, "name": self.repo.name}
        )

        response = self.client.get(url)
        assert response.status_code == 404  # no permissions

        assign_perm("plan.view_builds", self.user, self.planrepo)

        response = self.client.get(url)
        assert response.status_code == 200

    @pytest.mark.django_db
    def test_repo_orgs__as_superuser(self):
        self.client.force_login(self.superuser)
        url = reverse(
            "repo_orgs", kwargs={"owner": self.repo.owner, "name": self.repo.name}
        )

        response = self.client.get(url)
        assert response.status_code == 200

    @pytest.mark.django_db
    def test_repo_orgs__as_user(self):
        self.client.force_login(self.user)
        url = reverse(
            "repo_orgs", kwargs={"owner": self.repo.owner, "name": self.repo.name}
        )

        response = self.client.get(url)
        assert response.status_code == 404  # no permissions

        assign_perm("plan.org_login", self.user, self.planrepo)

        response = self.client.get(url)
        assert response.status_code == 200

    @pytest.mark.django_db
    def test_branch_detail__as_superuser(self):
        self.client.force_login(self.superuser)
        url = reverse(
            "branch_detail",
            kwargs={
                "owner": self.repo.owner,
                "name": self.repo.name,
                "branch": self.branch.name,
            },
        )

        response = self.client.get(url)
        assert response.status_code == 200

    @pytest.mark.django_db
    def test_branch_detail__as_user(self):
        self.client.force_login(self.user)
        url = reverse(
            "branch_detail",
            kwargs={
                "owner": self.repo.owner,
                "name": self.repo.name,
                "branch": self.branch.name,
            },
        )

        response = self.client.get(url)
        assert response.status_code == 404  # no permissions

        assign_perm("plan.view_builds", self.user, self.planrepo)

        response = self.client.get(url)
        assert response.status_code == 200

    @pytest.mark.django_db
    def test_commit_detail__as_superuser(self):
        self.client.force_login(self.superuser)
        url = reverse(
            "commit_detail",
            kwargs={"owner": self.repo.owner, "name": self.repo.name, "sha": "abc123"},
        )

        response = self.client.get(url)
        assert response.status_code == 200

    @pytest.mark.django_db
    def test_commit_detail__as_user(self):
        self.client.force_login(self.user)
        url = reverse(
            "commit_detail",
            kwargs={"owner": self.repo.owner, "name": self.repo.name, "sha": "abc123"},
        )

        response = self.client.get(url)
        assert response.status_code == 404  # no permissions

        assign_perm("plan.view_builds", self.user, self.planrepo)

        response = self.client.get(url)
        assert response.status_code == 200

    @pytest.mark.django_db
    @patch("metaci.repository.views.hmac")
    def test_validate_github_webhook__valid_request(self, hmac):
        request = RequestFactory()
        request.META = {"HTTP_X_HUB_SIGNATURE": "key=value"}
        request.body = None

        hmac.new.return_value = mock.Mock()
        hmac.compare_digest.return_value = True

        exception_raised = False
        try:
            views.validate_github_webhook(request)
        except Exception:
            exception_raised = True
        assert not exception_raised

        hmac.compare_digest.return_value = False
        with pytest.raises(PermissionDenied):
            views.validate_github_webhook(request)

    @pytest.mark.django_db
    @mock.patch("metaci.repository.views.validate_github_webhook")
    def test_github_webhook__repo_not_tracked(self, validate):
        self.client.force_login(self.user)
        url = reverse("github_webhook")
        push_data = {
            "repository": {"id": 1234567890},
            "ref": "refs/heads/feature-branch-1",
            "head_commit": "aR4Zd84F1i3No8",
        }

        response = self.client.post(
            url,
            data=json.dumps(push_data),
            content_type="application/json",
            HTTP_X_GITHUB_EVENT="push",
        )

        assert response.content == b"Not listening for this repository"

    @pytest.mark.django_db
    @mock.patch("metaci.repository.views.validate_github_webhook")
    def test_github_webhook__status_event(self, validate):
        self.plan.trigger = "status"
        self.plan.regex = None
        self.plan.commit_status_regex = "Build succeeded"
        self.plan.save()

        url = reverse("github_webhook")
        data = {
            "repository": {"id": self.repo.github_id},
            "ref": "refs/heads/feature-branch-1",
            "context": "Build succeeded",
            "state": "success",
            "sha": "aR4Zd84F1i3No8",
        }

        response = self.client.post(
            url,
            data=json.dumps(data),
            content_type="application/json",
            HTTP_X_GITHUB_EVENT="status",
        )

        assert response.content == b"OK"
        assert len(Build.objects.all()) == 1

    @pytest.mark.django_db
    def test_handle_github_push_webhook__no_branch_found(self):
        push_data = {
            "repository": {"id": self.repo.github_id},
            "head_commit": "aR4Zd84F1i3No8",
        }

        response = views.handle_github_push_or_status_webhook(
            "push", push_data, self.repo
        )
        assert response.status_code == 200
        assert response.content == b"No branch found"

    # TODO: this test is essentially a no-op and should be revised.
    @pytest.mark.django_db
    @mock.patch("metaci.repository.views.validate_github_webhook")
    def test_github_webhook__with_tag(self, validate):
        self.client.force_login(self.user)
        url = reverse("github_webhook")
        push_data = {
            "repository": {"id": self.repo.github_id},
            "ref": "refs/tags/beta",
            "head_commit": {"id": "aR4Zd84F1i3No8"},
        }

        response = self.client.post(
            url,
            data=json.dumps(push_data),
            content_type="application/json",
            HTTP_X_GITHUB_EVENT="push",
        )
        assert response.status_code == 200
        assert response.content == b"OK"

    @pytest.mark.django_db
    def test_handle_github_push_webhook__with_branch(self):
        branch_name = "feature-branch-1"
        push_data = {
            "repository": {"id": self.repo.github_id},
            "ref": f"refs/heads/{branch_name}",
            "head_commit": {"id": "aR4Zd84F1i3No8"},
        }

        response = views.handle_github_push_or_status_webhook(
            "push", push_data, self.repo
        )
        assert response.content == b"OK"
        assert Branch.objects.filter(name=branch_name).count() == 1

    @pytest.mark.django_db
    @patch("metaci.repository.views.set_merge_freeze_status_for_commit")
    def test_handle_github_pr_webhook__freeze_off(self, smfsc_mock):
        payload = {
            "repository": {"id": self.repo.github_id},
            "action": "opened",
            "pull_request": {
                "base": {"ref": "main", "repo": {"id": self.repo.github_id}},
                "head": {"repo": {"id": self.repo.github_id}, "sha": "abcdef123"},
            },
        }
        with patch.object(self.repo, "get_github_api") as api:
            api.return_value.default_branch = "main"
            response = views.handle_github_pr_webhook(
                "pull_request", payload, self.repo
            )
            assert response.content == b"OK"
            smfsc_mock.assert_called_once_with(
                api.return_value, "abcdef123", freeze=False
            )

    @pytest.mark.django_db
    @patch("metaci.repository.views.set_merge_freeze_status_for_commit")
    @patch("metaci.release.tasks.set_merge_freeze_status")
    def test_handle_github_pr_webhook__freeze_on(self, smfs_mock, smfsc_mock):
        cohort = ReleaseCohortFactory()
        ReleaseFactory(release_cohort=cohort, repo=self.repo)

        cohort.merge_freeze_start = datetime.now(tz=timezone.utc) - timedelta(
            minutes=20
        )
        cohort.status = ReleaseCohort.STATUS.active
        cohort.save()

        payload = {
            "repository": {"id": self.repo.github_id},
            "action": "opened",
            "pull_request": {
                "base": {"ref": "main", "repo": {"id": self.repo.github_id}},
                "head": {"repo": {"id": self.repo.github_id}, "sha": "abcdef123"},
            },
        }
        with patch.object(self.repo, "get_github_api") as api:
            api.return_value.default_branch = "main"
            response = views.handle_github_pr_webhook(
                "pull_request", payload, self.repo
            )
            assert response.content == b"OK"
            smfsc_mock.assert_called_once_with(
                api.return_value, "abcdef123", freeze=True
            )

    @pytest.mark.django_db
    @mock.patch("metaci.repository.views.validate_github_webhook")
    def test_github_webhook(self, validate):
        self.client.force_login(self.user)
        url = reverse("github_webhook")
        push_data = {
            "repository": {"id": self.repo.github_id},
            "ref": "refs/tags/beta",
            "head_commit": {"id": "aR4Zd84F1i3No8"},
        }

        with patch.object(
            views,
            "handle_github_push_or_status_webhook",
            wraps=views.handle_github_push_or_status_webhook,
        ) as handler_mock:
            self.client.post(
                url,
                data=json.dumps(push_data),
                content_type="application/json",
                HTTP_X_GITHUB_EVENT="push",
            )
            handler_mock.assert_called_once_with("push", push_data, self.repo)

        with patch.object(
            views,
            "handle_github_push_or_status_webhook",
            wraps=views.handle_github_push_or_status_webhook,
        ) as handler_mock:
            self.client.post(
                url,
                data=json.dumps(push_data),
                content_type="application/json",
                HTTP_X_GITHUB_EVENT="status",
            )
            handler_mock.assert_called_once_with("status", push_data, self.repo)

        with patch.object(
            views,
            "handle_github_pr_webhook",
            wraps=views.handle_github_push_or_status_webhook,
        ) as handler_mock:
            self.client.post(
                url,
                data=json.dumps(push_data),
                content_type="application/json",
                HTTP_X_GITHUB_EVENT="pull_request",
            )
            handler_mock.assert_called_once_with("pull_request", push_data, self.repo)

    @pytest.mark.django_db
    def test_get_repository(self):
        push_payload = {"repository": {"id": self.repo.github_id}}

        actual = views.get_repository(push_payload)
        assert actual.github_id == self.repo.github_id

    def test_get_branch_name_from_payload__no_ref(self):
        payload = {"not_ref": "12345"}
        branch_name = views.get_branch_name_from_payload(payload)
        assert branch_name is None

    def test_get_branch_name_from_payload(self):
        branch_name = "test-branch"
        branch_payload = {"ref": f"refs/heads/{branch_name}"}
        actual = views.get_branch_name_from_payload(branch_payload)
        assert actual == branch_name

        tag_name = "test-tag"
        tag_payload = {"ref": f"refs/tags/{tag_name}"}
        actual = views.get_branch_name_from_payload(tag_payload)
        assert actual == f"tag: {tag_name}"

    def test_get_branch_name_from_payload__branches(self):
        payload = {"branches": [{"name": "test-branch"}]}
        result = views.get_branch_name_from_payload(payload)
        assert result == "test-branch"

    @pytest.mark.django_db
    def test_get_or_create_branch(self):
        branch_name = "test-branch"
        BranchFactory(name=branch_name, is_removed=True)
        repo = RepositoryFactory(name="Test Repo")

        actual = views.get_or_create_branch(branch_name, repo)
        assert actual is not None

    @pytest.mark.django_db
    def test_get_release_if_applicable(self):
        payload = {"ref": "refs/tags/release-1", "head_commit": "abc123"}
        repo = RepositoryFactory(name="Test Repo")
        repo.release_tag_regex = "release-1"
        release = ReleaseFactory(repo=repo, git_tag="release-1")
        result = views.get_release_if_applicable(payload, repo)
        assert result == release

    def test_get_release_if_applicable__no_ref(self):
        payload = {}
        repo = mock.Mock()
        result = views.get_release_if_applicable(payload, repo)
        assert result is None

    def test_get_release_if_applicable__not_release_tag(self):
        payload = {"ref": "refs/tags/test-tag"}
        repo = mock.Mock(release_tag_regex=False)
        actual = views.get_release_if_applicable(payload, repo)
        assert actual is None

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

    @pytest.mark.django_db
    def test_create_builds__no_regex(self):
        """A plan without a regex, that has a trigger of 'commit',
        'tag', or 'status', should fail to create a build"""
        self.plan.regex = None
        self.plan.save()
        builds_before = len(Build.objects.all())
        views.create_builds("push", None, self.repo, self.branch, None)
        assert builds_before == len(Build.objects.all())
