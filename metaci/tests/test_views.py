import pytest
from django.test import Client, TestCase
from django.urls import reverse

from metaci.conftest import StaffSuperuserFactory, UserFactory


class TestRepositoryViews(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.superuser = StaffSuperuserFactory()
        cls.user = UserFactory()
        super().setUpTestData()

    @pytest.mark.django_db
    def test_cohorts_link_absent_for_anon_user(self):
        self.client = Client()
        url = reverse("repo_list")

        response = self.client.get(url)
        assert b"Release Cohorts" not in response.content

    @pytest.mark.django_db
    def test_cohorts_link_shows_for_superuser(self):
        self.client.force_login(self.superuser)
        url = reverse("repo_list")

        response = self.client.get(url)
        assert b"Release Cohorts" in response.content

    @pytest.mark.django_db
    def test_cohorts_link_absent_for_ordinary_user(self):
        self.client.force_login(self.user)
        url = reverse("repo_list")

        response = self.client.get(url)
        assert b"Release Cohorts" not in response.content
