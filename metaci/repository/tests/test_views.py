import json
from unittest import mock

import pytest
from django.test import Client, TestCase
from django.test.client import RequestFactory
from django.urls import reverse
from guardian.shortcuts import assign_perm

from metaci.build.models import Build
from metaci.conftest import (
    BranchFactory,
    BuildFactory,
    BuildFlowFactory,
    PlanFactory,
    PlanRepositoryFactory,
    RepositoryFactory,
    StaffSuperuserFactory,
    TestResultFactory,
    UserFactory,
)
from metaci.plan.models import Plan, PlanRepository
from metaci.repository import views
from metaci.repository.models import Repository


class TestRepositoryViews(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = Client()
        cls.superuser = StaffSuperuserFactory()
        cls.user = UserFactory()
        cls.plan = PlanFactory(name="Plan1")
        cls.repo = RepositoryFactory(name="PublicRepo")
        cls.planrepo = PlanRepositoryFactory(plan=cls.plan, repo=cls.repo)
        cls.branch = BranchFactory(name="test-branch", repo=cls.repo)
        super(TestRepositoryViews, cls).setUpClass()

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
    def test_repo_perf__as_superuser(self):
        self.client.force_login(self.superuser)
        url = reverse(
            "repo_perf", kwargs={"owner": self.repo.owner, "name": self.repo.name}
        )

        response = self.client.get(url)
        assert response.status_code == 200

    @pytest.mark.django_db
    def test_repo_perf__as_user(self):
        self.client.force_login(self.user)
        url = reverse(
            "repo_perf", kwargs={"owner": self.repo.owner, "name": self.repo.name}
        )

        response = self.client.get(url)
        assert response.status_code == 404  # no permissions

        assign_perm("plan.view_builds", self.user, self.planrepo)

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
    def test_get_repository(self):
        push_payload = {"repository": {"id": self.repo.github_id}}

        actual = views.get_repository(push_payload)
        assert actual.github_id == self.repo.github_id

    def test_get_branch_name_from_payload__no_ref(self):
        payload = {"not_ref": "12345"}
        branch_name = views.get_branch_name_from_payload(payload)
        assert branch_name == None

    def test_get_branch_name_from_payload(self):
        branch_name = "test-branch"
        branch_payload = {"ref": f"refs/heads/{branch_name}"}
        actual = views.get_branch_name_from_payload(branch_payload)
        assert actual == branch_name

        tag_name = "test-tag"
        tag_payload = {"ref": f"refs/tags/{tag_name}"}
        actual = views.get_branch_name_from_payload(tag_payload)
        assert actual == f"tag: {tag_name}"

    @pytest.mark.django_db
    def test_get_or_create_branch(self):
        branch_name = "test-branch"
        branch = BranchFactory(name=branch_name, is_removed=True)
        repo = RepositoryFactory(name="Test Repo")

        actual = views.get_or_create_branch(branch_name, repo)
        assert actual is not None

    @pytest.mark.django_db
    def test_get_or_create_release(self):
        tag = "release-tag"
        repo = RepositoryFactory(name="Test Repo")
        push_payload = {"head_commit": {"id": "asdf1234"}}

        actual = views.get_or_create_release(push_payload, tag, repo)
        assert actual is not None

    @mock.patch("metaci.repository.views.tag_is_release")
    @mock.patch("metaci.repository.views.get_or_create_release")
    def test_get_release_applicable(self, get_release, tag_is_release):
        push = {"ref": "refs/tags/release-1", "head_commit": "abc123"}
        repo = mock.Mock()
        repo.release_tag_regex = r"refs/tags/release-1"

        get_release.return_value = True
        tag_is_release.return_value = True

        release = views.get_release_if_applicable(push, repo)

        assert release == True

    def test_get_release_not_applicable(self):
        push = {"ref": "refs/tags/test-tag"}
        repo = mock.Mock(release_tag_regex=False)
        actual = views.get_release_if_applicable(push, repo)
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
