from unittest import mock

import pytest
from django.urls import reverse
from guardian.shortcuts import assign_perm

from metaci.fixtures.factories import RebuildFactory


@pytest.mark.django_db
class TestBuildViews:
    def test_build_list(self, client, superuser, data):
        client.force_login(superuser)
        url = reverse("home")
        response = client.get(url, {"repo": data["repo"].name})

        assert response.status_code == 200

    def test_build_detail__permission_denied(self, client, user, data):
        client.force_login(user)
        url = reverse("build_detail", kwargs={"build_id": data["build"].id})
        response = client.get(url)

        assert response.status_code == 403

    def test_build_detail(self, client, superuser, data):
        client.force_login(superuser)
        url = reverse("build_detail", kwargs={"build_id": data["build"].id})
        response = client.get(url)

        assert response.status_code == 200

    def test_build_detail_flows(self, client, superuser, data):
        client.force_login(superuser)
        url = reverse("build_detail_flows", kwargs={"build_id": data["build"].id})
        response = client.get(url)

        assert response.status_code == 200

    def test_build_detail_tests(self, client, superuser, data):
        client.force_login(superuser)
        url = reverse("build_detail_tests", kwargs={"build_id": data["build"].id})
        response = client.get(url)

        assert response.status_code == 200

    def test_build_detail_rebuilds(self, client, superuser, data):
        client.force_login(superuser)
        url = reverse("build_detail_rebuilds", kwargs={"build_id": data["build"].id})
        response = client.get(url)

        assert response.status_code == 200

    def test_build_detail_org(self, client, superuser, data):
        client.force_login(superuser)
        url = reverse("build_detail_org", kwargs={"build_id": data["build"].id})
        response = client.get(url)

        assert response.status_code == 200

    def test_build_detail_org__rebuild(self, client, superuser, data):
        rebuild = RebuildFactory(build=data["build"])
        client.force_login(superuser)
        url = reverse(
            "build_detail_org",
            kwargs={"build_id": data["build"].id, "rebuild_id": rebuild.id},
        )
        response = client.get(url)

        assert response.status_code == 200

    def test_build_detail_org__permission_denied(self, client, user, data):
        # This permission is checked for in build_detail_base()
        assign_perm("plan.view_builds", user, data["planrepo"])
        client.force_login(user)
        url = reverse("build_detail_org", kwargs={"build_id": data["build"].id})
        response = client.get(url)

        assert response.status_code == 403

    def test_build_detail_qa(self, client, superuser, data):
        client.force_login(superuser)
        url = reverse("build_detail_qa", kwargs={"build_id": data["build"].id})
        response = client.get(url)

        assert response.status_code == 200

    @mock.patch("metaci.build.views.QATestingForm")
    def test_build_detail_qa__post(self, QATestingForm, client, superuser, data):
        client.force_login(superuser)
        url = reverse("build_detail_qa", kwargs={"build_id": data["build"].id})
        response = client.post(url)

        assert response.status_code == 200

    def test_build_detail_qa__permission_denied(self, client, user, data):
        # This permission is checked for in build_detail_base()
        assign_perm("plan.view_builds", user, data["planrepo"])
        client.force_login(user)
        url = reverse("build_detail_qa", kwargs={"build_id": data["build"].id})
        response = client.get(url)

        assert response.status_code == 403

    def test_build_rebuild(self, client, superuser, data):
        client.force_login(superuser)
        url = reverse("build_rebuild", kwargs={"build_id": data["build"].id})
        response = client.get(url)

        assert response.status_code == 302

    def test_build_rebuild__permission_denied(self, client, user, data):
        client.force_login(user)
        url = reverse("build_rebuild", kwargs={"build_id": data["build"].id})
        response = client.get(url)

        assert response.status_code == 403

    def test_build_search(self, client, superuser, data):
        client.force_login(superuser)
        url = reverse("build_search")
        response = client.get(url, {"q": data["build"]})

        assert response.status_code == 200
