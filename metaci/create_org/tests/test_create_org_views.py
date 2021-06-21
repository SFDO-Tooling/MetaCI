import pytest
from django.urls import reverse
from guardian.shortcuts import assign_perm

from metaci.conftest import (
    PlanFactory,
    PlanRepositoryFactory,
    RepositoryFactory,
    UserFactory,
)


@pytest.fixture
def planrepos(db):
    repo = RepositoryFactory()
    plan1 = PlanFactory(role="scratch")
    plan2 = PlanFactory(role="qa")
    planrepo1 = PlanRepositoryFactory(repo=repo, plan=plan1)
    planrepo2 = PlanRepositoryFactory(repo=repo, plan=plan2)
    return planrepo1, planrepo2


class TestCreateOrgViews:
    @pytest.mark.django_db
    def test_create_org__as_superuser(self, admin_client, planrepos):
        url = reverse("create_org")
        response = admin_client.get(url)
        assert response.status_code == 200

    @pytest.mark.django_db
    def test_create_org__as_user_not_allowed(self, client, planrepos):
        user = UserFactory()
        client.force_login(user)
        response = client.get(reverse("create_org"))
        assert response.status_code == 403

    @pytest.mark.django_db
    def test_create_org__as_user_allowed(self, client, planrepos):
        user = UserFactory()
        assign_perm("plan.run_plan", user, planrepos[0])

        client.force_login(user)
        response = client.get(reverse("create_org"))
        assert response.status_code == 200

    @pytest.mark.django_db
    def test_scratch_org__as_superuser(self, admin_client, planrepos):
        url = reverse("create_org_scratch")
        response = admin_client.get(url)
        assert response.status_code == 200

    @pytest.mark.django_db
    def test_scratch_org__as_user_not_allowed(self, client, planrepos):
        user = UserFactory()
        client.force_login(user)
        response = client.get(reverse("create_org_scratch"))
        assert response.status_code == 403

    @pytest.mark.django_db
    def test_scratch_org__as_user_allowed(self, client, planrepos):
        user = UserFactory()
        assign_perm("plan.run_plan", user, planrepos[0])

        client.force_login(user)
        response = client.get(reverse("create_org_scratch"))
        assert response.status_code == 200

    @pytest.mark.django_db
    def test_qa_org__as_superuser(self, admin_client, planrepos):
        url = reverse("create_org_qa")
        response = admin_client.get(url)
        assert response.status_code == 200

    @pytest.mark.django_db
    def test_qa_org__as_user_not_allowed(self, client, planrepos):
        user = UserFactory()
        client.force_login(user)
        response = client.get(reverse("create_org_qa"))
        assert response.status_code == 403

    @pytest.mark.django_db
    def test_qa_org__as_user_allowed(self, client, planrepos):
        user = UserFactory()
        assign_perm("plan.run_plan", user, planrepos[1])

        # logged in w/o perms
        client.force_login(user)
        response = client.get(reverse("create_org_qa"))
        assert response.status_code == 200
