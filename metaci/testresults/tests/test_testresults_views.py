import pytest
from django.test import Client, TestCase
from django.urls import reverse

from metaci.conftest import (
    BuildFactory,
    BuildFlowFactory,
    PlanFactory,
    PlanRepositoryFactory,
    RepositoryFactory,
    StaffSuperuserFactory,
    TestClassFactory,
    TestMethodFactory,
    TestResultFactory,
    UserFactory,
)


class TestTestCoverageViews(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.client = Client()
        cls.user = UserFactory()
        cls.superuser = StaffSuperuserFactory()
        cls.repo = RepositoryFactory()
        cls.plan = PlanFactory()
        cls.planrepo = PlanRepositoryFactory(plan=cls.plan, repo=cls.repo)
        cls.build = BuildFactory(planrepo=cls.planrepo)
        cls.testclass = TestClassFactory(repo=cls.repo)
        cls.testmethod = TestMethodFactory(testclass=cls.testclass)
        cls.testmethod.test_dashboard = True
        cls.testmethod.save()
        cls.testresult = TestResultFactory(method=cls.testmethod)
        cls.testresult.build = cls.build
        cls.testresult.save()
        cls.buildflow = BuildFlowFactory(build=cls.build, flow="flow-one")
        return super(TestTestCoverageViews, cls).setUpTestData()

    @pytest.mark.django_db
    def test_build_flow_tests(self):
        self.client.force_login(self.superuser)

        url = reverse(
            "build_flow_tests", kwargs={"build_id": self.build.id, "flow": "flow-one"},
        )
        response = self.client.get(url)

        assert response.status_code == 200

    @pytest.mark.django_db
    def test_test_dashboard__superuser(self):
        self.client.force_login(self.superuser)

        url = reverse(
            "test_dashboard",
            kwargs={"repo_owner": self.repo.owner, "repo_name": self.repo.name},
        )
        response = self.client.get(url)

        assert response.status_code == 200
