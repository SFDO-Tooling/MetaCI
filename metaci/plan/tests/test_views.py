import pytest
from unittest import mock

from django.test import Client
from django.urls import reverse
from django.core.exceptions import PermissionDenied

from metaci.plan import views
from metaci.fixtures.factories import BranchFactory


@pytest.mark.django_db
class TestPlanViews:
    client = Client()

    def test_plan_list(self, data, superuser):
        self.client.force_login(superuser)
        url = reverse("plan_list")
        response = self.client.get(url)

        assert response.status_code == 200

    def test_plan_detail(self, data, superuser):
        self.client.force_login(superuser)
        url = reverse("plan_detail", kwargs={"plan_id": data["plan"].id})
        response = self.client.get(url)

        assert response.status_code == 200

    def test_plan_detail_repo(self, data, superuser):
        self.client.force_login(superuser)
        url = reverse(
            "plan_detail_repo",
            kwargs={
                "plan_id": data["plan"].id,
                "repo_owner": data["repo"].owner,
                "repo_name": data["repo"].name,
            },
        )
        response = self.client.get(url)

        assert response.status_code == 200

    def test_plan_run(self, data, superuser):
        self.client.force_login(superuser)
        url = reverse("plan_run", kwargs={"plan_id": data["plan"].id})
        response = self.client.get(url)

        assert response.status_code == 200

    def test_plan_run__permission_denied(self, data, user):
        self.client.force_login(user)
        url = reverse("plan_run", kwargs={"plan_id": data["plan"].id})
        response = self.client.get(url)

        assert response.status_code == 403

    @mock.patch("metaci.plan.forms.RunPlanForm._get_branch_choices")
    def test_plan_run_repo(self, branchChoices, data, superuser):
        self.client.force_login(superuser)
        url = reverse(
            "plan_run_repo",
            kwargs={
                "plan_id": data["plan"].id,
                "repo_owner": data["repo"].owner,
                "repo_name": data["repo"].name,
            },
        )
        BranchFactory(name="feature/branch-a", repo=data["repo"])
        branchChoices = ["feature/branch-a", "feature/branch-b"]
        response = self.client.get(url)

        assert response.status_code == 200

        # response = self.client.post(url)
        # assert response.status_code == 301

    def test_plan_run_repo__permission_denied(self, data, user):
        self.client.force_login(user)
        url = reverse(
            "plan_run_repo",
            kwargs={
                "plan_id": data["plan"].id,
                "repo_owner": data["repo"].owner,
                "repo_name": data["repo"].name,
            },
        )
        response = self.client.get(url)
        assert response.status_code == 403
