import pytest
from django.test import Client
from django.urls import reverse

from metaci.testresults import views


class TestTestCoverageViews:
    client = Client()

    @pytest.mark.django_db
    def test_build_flow_tests(self, data, superuser):
        self.client.force_login(superuser)

        url = reverse(
            "build_flow_tests",
            kwargs={"build_id": data["build"].id, "flow": "flow-one"},
        )
        response = self.client.get(url, {"sort": "method__testclass__name"})

        assert response.status_code == 200

    @pytest.mark.django_db
    def test_set_percent_data(self, data):
        result = data["testresult"]
        column = "percent"

        column_data = {"heading": "worst_limit", "status": "activate", "value": 40}
        views.set_percent_data(result, column, column_data)
        assert column_data["status"] == "success"

        column_data = {"heading": "worst_limit", "status": "activate", "value": 51}
        views.set_percent_data(result, column, column_data)
        assert column_data["status"] == "info"

        column_data = {"heading": "worst_limit", "status": "activate", "value": 71}
        views.set_percent_data(result, column, column_data)
        assert column_data["status"] == "warning"

        column_data = {"heading": "worst_limit", "status": "activate", "value": 81}
        views.set_percent_data(result, column, column_data)
        assert column_data["status"] == "danger"

    @pytest.mark.django_db
    def test_test_result_detail__superuser(self, data, superuser):
        self.client.force_login(superuser)

        url = reverse("test_result_detail", kwargs={"result_id": data["testresult"].id})
        response = self.client.get(url)

        assert response.status_code == 200

    @pytest.mark.django_db
    def test_result_robot__no_robot_xml(self, data, superuser):
        self.client.force_login(superuser)

        url = reverse("test_result_robot", kwargs={"result_id": data["testresult"].id})
        response = self.client.get(url)

        assert response.status_code == 200
        assert b"No robot_xml" in response.content

    @pytest.mark.skip
    @pytest.mark.django_db
    def test_result_robot(self, data, superuser):
        # TODO: Need sample robot.xml file to set to TestResult.robot_xml attribute in data_fixtures
        self.client.force_login(superuser)

        url = reverse("test_result_robot", kwargs={"result_id": data["testresult"].id})
        response = self.client.get(url)

        assert response.status_code == 200

    @pytest.mark.django_db
    def test_test_method_peek__superuser(self, data, superuser):
        self.client.force_login(superuser)

        url = reverse("test_method_peek", kwargs={"method_id": data["testmethod"].id})
        response = self.client.get(url)

        assert response.status_code == 200

    @pytest.mark.django_db
    def test_test_method_trend__superuser(self, data, superuser):
        self.client.force_login(superuser)
        url = reverse("test_method_trend", kwargs={"method_id": data["testmethod"].id})
        response = self.client.get(url)

        assert response.status_code == 200

    @pytest.mark.skip
    @pytest.mark.django_db
    def test_build_flow_compare__superuser(self, data, superuser):
        # TODO: NoReverseMatch troubleshooting
        self.client.force_login(superuser)
        url = reverse("build_flow_compare")
        response = self.client.get(
            url,
            {"buildflow1": data["buildflow"].id, "buildflow2": data["buildflow"].id,},
        )
        assert response.status_code == 200

    @pytest.mark.skip
    @pytest.mark.django_db
    def test_test_dashboard__superuser(self, data, superuser):
        """Currently failing because test_dashboard has a fileter
        that references a testresult field on TestMethod objs
        have no clue what the code is trying to do."""
        self.client.force_login(superuser)

        url = reverse(
            "test_dashboard",
            kwargs={"repo_owner": data["repo"].owner, "repo_name": data["repo"].name},
        )
        response = self.client.get(url)

        assert response.status_code == 200
