from unittest import mock

import pytest
from django.urls import reverse

from metaci.fixtures.factories import BranchFactory
from metaci.fixtures.factories import ReleaseFactory


@pytest.mark.django_db
class TestPlanViews:
    def test_plan_list(self, client, data, superuser):
        client.force_login(superuser)
        url = reverse("plan_list")
        response = client.get(url)

        assert response.status_code == 200

    def test_plan_detail(self, client, data, superuser):
        client.force_login(superuser)
        url = reverse("plan_detail", kwargs={"plan_id": data["plan"].id})
        response = client.get(url)

        assert response.status_code == 200

    def test_plan_detail_repo(self, client, data, superuser):
        client.force_login(superuser)
        url = reverse(
            "plan_detail_repo",
            kwargs={
                "plan_id": data["plan"].id,
                "repo_owner": data["repo"].owner,
                "repo_name": data["repo"].name,
            },
        )
        response = client.get(url)

        assert response.status_code == 200

    def test_plan_run(self, client, data, superuser):
        client.force_login(superuser)
        url = reverse("plan_run", kwargs={"plan_id": data["plan"].id})
        response = client.get(url)

        assert response.status_code == 200

    def test_plan_run__permission_denied(self, client, data, user):
        client.force_login(user)
        url = reverse("plan_run", kwargs={"plan_id": data["plan"].id})
        response = client.get(url)

        assert response.status_code == 403

    @mock.patch("metaci.plan.forms.RunPlanForm._get_branch_choices")
    def test_plan_run_repo__get(self, branchChoices, client, data, superuser):
        client.force_login(superuser)
        url = reverse(
            "plan_run_repo",
            kwargs={
                "plan_id": data["plan"].id,
                "repo_owner": data["repo"].owner,
                "repo_name": data["repo"].name,
            },
        )
        response = client.get(url)

        assert response.status_code == 200

    @mock.patch("metaci.plan.views.RunPlanForm")
    def test_plan_run_repo__post(self, RunPlanForm, client, data, superuser):
        client.force_login(superuser)
        url = reverse(
            "plan_run_repo",
            kwargs={
                "plan_id": data["plan"].id,
                "repo_owner": data["repo"].owner,
                "repo_name": data["repo"].name,
            },
        )

        RunPlanForm.return_value = mock.Mock(
            create_build=mock.Mock(return_value=data["build"])
        )
        response = client.post(
            url, {"branch": BranchFactory(name="feature/branch-a", repo=data["repo"])}
        )
        assert response.status_code == 302

    def test_plan_run_repo__no_change_case(self, mocker, client, data, superuser):
        mocker.patch("metaci.plan.forms.RunPlanForm._get_branch_choices")
        mocker.patch(
            "metaci.plan.forms.settings", METACI_ENFORCE_RELEASE_CHANGE_CASE=True
        )
        data["plan"].role = "release"
        data["plan"].save()

        client.force_login(superuser)
        url = reverse(
            "plan_run_repo",
            kwargs={
                "plan_id": data["plan"].id,
                "repo_owner": data["repo"].owner,
                "repo_name": data["repo"].name,
            },
        )

        response = client.post(
            url,
            {
                "branch": BranchFactory(name="feature/branch-a", repo=data["repo"]).pk,
                "release": ReleaseFactory(repo=data["repo"]).pk,
            },
        )
        assert response.status_code == 200
        assert b"This release does not link to a change case." in response.content

    def test_plan_run_repo__permission_denied(self, client, data, user):
        client.force_login(user)
        url = reverse(
            "plan_run_repo",
            kwargs={
                "plan_id": data["plan"].id,
                "repo_owner": data["repo"].owner,
                "repo_name": data["repo"].name,
            },
        )
        response = client.get(url)
        assert response.status_code == 403
