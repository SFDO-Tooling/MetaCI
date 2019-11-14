import json
import pytest
from unittest import mock
from django.test import TestCase, Client
from django.test.client import RequestFactory
from django.urls import reverse

from metaci.repository import views
from metaci.plan.models import Plan
from metaci.build.models import Build
from metaci.repository.models import Repository

from metaci.conftest import (
    RepositoryFactory,
    BranchFactory,
    PlanFactory,
    BuildFactory,
    BuildFlowFactory,
    TestResultFactory,
    PlanRepositoryFactory,
    StaffSuperuserFactory,
)


class TestGithubPushWebHook(TestCase):
    @classmethod
    def setUpClass(cls):
        p1 = PlanFactory(name="Plan1")
        p2 = PlanFactory(name="Plan2")
        r1 = RepositoryFactory(name="PublicRepo")
        r2 = RepositoryFactory(name="PrivateRepo")
        public_pr = PlanRepositoryFactory(plan=p1, repo=r1)
        # assign_perm("plan.view_builds", Group.objects.get(name="Public"), public_pr)
        pr2 = PlanRepositoryFactory(plan=p2, repo=r2)
        BranchFactory(name="Branch1", repo=r1)
        BranchFactory(name="Branch2", repo=r2)
        private_build = BuildFactory(repo=r2, plan=p2, planrepo=pr2)
        private_bff = BuildFlowFactory(build=private_build)
        public_build = BuildFactory(repo=r2, plan=p2, planrepo=pr2)
        public_bff = BuildFlowFactory(build=public_build)
        BuildFlowFactory(flow="Flow2")
        TestResultFactory(build_flow=private_bff, method__name="Private1")
        TestResultFactory(build_flow=private_bff, method__name="Private2")
        TestResultFactory(build_flow=public_bff, method__name="Public1")
        TestResultFactory(build_flow=public_bff, method__name="Public2")

    @pytest.mark.django_db
    def test_repo_detail(self):
        response = Client().get(reverse("repo-detail"))
        assert response.status_code == 200

    @pytest.mark.django_db
    @pytest.mark.skip
    @mock.patch("metaci.repository.views.validate_github_webhook")
    def test_github_push_webhook(self, validate_webhook):
        plane_repo = PlanRepositoryFactory()

        body = {"ref": "refs/heads/test-branch", "repository": {"id": repo.github_id}}
        webhook_request = RequestFactory().post(
            "/webhook/github/push", json.dumps(body), content_type="application/json"
        )

        response = views.github_push_webhook(webhook_request)
        assert response is not None

    @pytest.mark.django_db
    def test_get_repository(self):
        repo = RepositoryFactory(name="TestRepo")
        push_payload = {"repository": {"id": repo.github_id}}

        actual = views.get_repository(push_payload)
        assert actual.github_id == repo.github_id

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

    @pytest.mark.django_db
    def test_create_builds(self):
        plan_repo = PlanRepositoryFactory()
        repo = Repository.objects.get(pk=1)
        plan = Plan.objects.get(pk=1)
        plan.active = True
        plan.trigger = "tag"
        plan.save()

        assert Build.objects.all().count() == 0
        views.create_builds(mock.Mock(), repo, "test-branch", mock.Mock())
        # assert Build.objects.all().count() == 1
