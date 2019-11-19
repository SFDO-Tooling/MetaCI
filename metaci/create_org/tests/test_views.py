import pytest
from django.test import Client, TestCase
from django.urls import reverse
from guardian.shortcuts import assign_perm

from metaci.conftest import (
    PlanFactory,
    PlanRepositoryFactory,
    RepositoryFactory,
    StaffSuperuserFactory,
    UserFactory,
)


class TestCreateOrgViews(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.client = Client()
        cls.superuser = StaffSuperuserFactory()
        cls.user = UserFactory()
        cls.repo = RepositoryFactory()
        cls.plan1 = PlanFactory()
        cls.plan1.role = "scratch"
        cls.plan1.save()
        cls.plan2 = PlanFactory()
        cls.plan2.role = "qa"
        cls.plan2.save()
        cls.planrepo1 = PlanRepositoryFactory(repo=cls.repo, plan=cls.plan1)
        cls.planrepo2 = PlanRepositoryFactory(repo=cls.repo, plan=cls.plan2)
        super(TestCreateOrgViews, cls).setUpTestData()

    @pytest.mark.django_db
    def test_create_org__as_superuser(self):
        self.client.force_login(self.superuser)
        url = reverse("create_org")
        response = self.client.get(url)
        assert response.status_code == 200

    @pytest.mark.django_db
    def test_create_org__as_user(self):
        # not logged in
        url = reverse("create_org")
        response = self.client.get(url)

        # logged in w/o perms
        self.client.force_login(self.user)
        response = self.client.get(url)

        # PermissionDenied exception
        # https://docs.djangoproject.com/en/2.2/ref/views/#the-403-http-forbidden-view
        response.status_code == 403

        # assign user perms
        assign_perm("plan.run_plan", self.user, self.planrepo1)

        response = self.client.get(url)
        assert response.status_code == 200

    @pytest.mark.django_db
    def test_scratch_org__as_superuser(self):
        self.client.force_login(self.superuser)
        url = reverse("create_org_scratch")
        response = self.client.get(url)
        assert response.status_code == 200

    @pytest.mark.django_db
    def test_scratch_org__as_user(self):
        # not logged in
        url = reverse("create_org_scratch")
        response = self.client.get(url)

        # logged in w/o perms
        self.client.force_login(self.user)
        response = self.client.get(url)

        # PermissionDenied exception
        # https://docs.djangoproject.com/en/2.2/ref/views/#the-403-http-forbidden-view
        response.status_code == 403

        # assign user perms
        assign_perm("plan.run_plan", self.user, self.planrepo1)

        response = self.client.get(url)
        assert response.status_code == 200

    @pytest.mark.django_db
    def test_qa_org__as_superuser(self):
        self.client.force_login(self.superuser)
        url = reverse("create_org_qa")
        response = self.client.get(url)
        assert response.status_code == 200

    @pytest.mark.django_db
    def test_qa_org__as_user(self):
        # not logged in
        url = reverse("create_org_qa")
        response = self.client.get(url)

        # logged in w/o perms
        self.client.force_login(self.user)
        response = self.client.get(url)

        # PermissionDenied exception
        # https://docs.djangoproject.com/en/2.2/ref/views/#the-403-http-forbidden-view
        response.status_code == 403

        # assign user perms
        assign_perm("plan.run_plan", self.user, self.planrepo2)

        response = self.client.get(url)
        assert response.status_code == 200
