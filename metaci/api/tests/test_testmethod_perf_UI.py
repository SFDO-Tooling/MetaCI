from metaci.conftest import (
    StaffSuperuserFactory,
    #  BuildFactory,
    RepositoryFactory,
    BranchFactory,
    PlanFactory,
    BuildFlowFactory,
)

from django.urls import reverse

from rest_framework.test import APIClient, APITestCase

from .test_testmethod_perf import _TestingHelpers


class TestTestMethodPerfUI_RESTAPI(APITestCase, _TestingHelpers):
    @classmethod
    def setUpClass(cls):
        cls.client, cls.user = cls.make_user_and_client()
        super().setUpClass()
        p1 = PlanFactory(name="Plan1")
        p2 = PlanFactory(name="Plan2")
        r1 = RepositoryFactory(name="Repo1")
        r2 = RepositoryFactory(name="Repo2")
        b1 = BranchFactory(name="Branch1", repo=r1)
        b2 = BranchFactory(name="Branch2", repo=r2)
        bf1 = BuildFlowFactory(flow="Flow1")
        bf2 = BuildFlowFactory(flow="Flow2")
        (p1, p2, r1, r2, b1, b2, bf1, bf2)  # shut up linter

    def setUp(self):
        self.client.force_authenticate(self.user)

    def debugmsg(self, *args):
        print(*args)  # Pytest does useful stuff with stdout, better than logger data

    @classmethod
    def make_user_and_client(cls):
        user = StaffSuperuserFactory()
        client = APIClient()
        client.force_authenticate(user)
        response = client.get("/api/")
        assert response.status_code == 200, response.content
        return client, user

    def api_url(self):
        return reverse("testmethod_perf_UI-list")

    def find_by(self, fieldname, objs, value):
        if type(objs) == dict:
            objs = objs.get("results", objs)
        return next((x for x in objs if x[fieldname] == value), None)

    def get_api_results(self):
        response = self.client.get(self.api_url())
        self.assertEqual(response.status_code, 200)
        obj = response.json()
        return obj

    def test_api_schema_view(self):
        response = self.client.get("/api/")
        self.debugmsg(response)
        self.assertEqual(response.status_code, 200)
        self.assertIn("application/json", response["content-type"])
        self.assertIn(bytes(self.api_url(), "ascii"), response.content)

    def test_includable_fields(self):
        obj = self.get_api_results()
        includable_fields = obj["includable_fields"]
        self.assertIn("duration_average", includable_fields)
        self.assertIn("count", includable_fields)

    def test_group_by_fields(self):
        obj = self.get_api_results()
        group_by_fields = obj["group_by_fields"]
        self.assertIn("repo", group_by_fields)
        self.assertIn("branch", group_by_fields)
        self.assertIn("plan", group_by_fields)
        self.assertIn("flow", group_by_fields)

    def test_buildflow_filters(self):
        obj = self.get_api_results()
        buildflow_filters = obj["buildflow_filters"]
        self.assertIn("repo", buildflow_filters)
        self.assertIn("branch", buildflow_filters)
        self.assertIn("plan", buildflow_filters)
        self.assertIn("flow", buildflow_filters)
        self.assertIn("Repo1", buildflow_filters["repo"]["choices"])
        self.assertIn("Repo2", buildflow_filters["repo"]["choices"])
        self.assertIn("Plan1", buildflow_filters["plan"]["choices"])
        self.assertIn("Plan2", buildflow_filters["plan"]["choices"])
        self.assertIn("Branch1", buildflow_filters["branch"]["choices"])
        self.assertIn("Branch2", buildflow_filters["branch"]["choices"])
        self.assertIn("Flow1", buildflow_filters["flow"]["choices"])
        self.assertIn("Flow2", buildflow_filters["flow"]["choices"])
