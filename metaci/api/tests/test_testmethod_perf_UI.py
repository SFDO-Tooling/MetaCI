import pytest
from django.urls import reverse
from rest_framework.test import APITestCase

from metaci.conftest import (
    BranchFactory,
    BuildFlowFactory,
    PlanFactory,
    RepositoryFactory,
)

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

    def api_url(self):
        return reverse("testmethod_perf_UI-list")

    def test_api_schema_view(self):
        response = self.client.get("/api/")
        self.debugmsg(response)
        self.assertEqual(response.status_code, 200)
        self.assertIn("application/json", response["content-type"])
        self.assertIn(bytes(self.api_url(), "ascii"), response.content)

    @pytest.mark.skip(reason="Major refactor. Update the test soon.")
    def test_includable_fields(self):
        obj = self.get_api_results()
        includable_fields = keys(obj["includable_fields"])
        self.assertIn("duration_average", includable_fields)
        self.assertIn("count", includable_fields)

    @pytest.mark.skip(reason="Major refactor. Update the test soon.")
    def test_buildflow_filters(self):
        obj = self.get_api_results()
        buildflow_filters = obj["buildflow_filters"]

        self.assertIn("choice_filters", buildflow_filters)
        self.assertIn("other_buildflow_filters", buildflow_filters)

        choice_filters = buildflow_filters["choice_filters"]
        self.assertIn("repo", choice_filters)
        self.assertIn("branch", choice_filters)
        self.assertIn("plan", choice_filters)
        self.assertIn("flow", choice_filters)
        self.assertIn("recentdate", choice_filters)

        other_buildflow_filters = buildflow_filters["other_buildflow_filters"]

        self.assertIn("daterange", other_buildflow_filters)

        self.assertIn("Repo1", keys(choice_filters["repo"]["choices"]))
        self.assertIn("Repo2", keys(choice_filters["repo"]["choices"]))
        self.assertIn("Plan1", keys(choice_filters["plan"]["choices"]))
        self.assertIn("Plan2", keys(choice_filters["plan"]["choices"]))
        self.assertIn("Branch1", keys(choice_filters["branch"]["choices"]))
        self.assertIn("Branch2", keys(choice_filters["branch"]["choices"]))
        self.assertIn("Flow1", keys(choice_filters["flow"]["choices"]))
        self.assertIn("Flow2", keys(choice_filters["flow"]["choices"]))


def keys(list_of_pairs):
    return [pair[0] for pair in list_of_pairs]
