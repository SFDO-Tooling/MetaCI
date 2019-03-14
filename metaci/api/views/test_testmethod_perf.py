from urllib.parse import urlencode
import random

from rest_framework.test import APIClient, APITestCase

import factory
import factory.fuzzy

from django.urls import reverse
from rest_framework.test import APIClient

from metaci.plan.models import Plan, PlanRepository
from metaci.testresults.models import TestResult, TestMethod, TestClass
from metaci.build.models import BuildFlow, Build
from metaci.repository.models import Branch, Repository

from metaci.users.models import User
from rest_framework.authtoken.models import Token


class PlanFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Plan


class RepositoryFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Repository

    github_id = 1234


class PlanRepositoryFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = PlanRepository

    plan = factory.SubFactory(PlanFactory)
    repo = factory.SubFactory(RepositoryFactory)


class Branch(factory.django.DjangoModelFactory):
    class Meta:
        model = Branch


class BuildFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Build

    plan = factory.SubFactory(PlanFactory)
    repo = factory.SubFactory(RepositoryFactory)


class BuildFlowFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = BuildFlow

    class Params:
        flow = "gowiththe"

    build = factory.SubFactory(BuildFactory)


class TestClassFactory(factory.django.DjangoModelFactory):
    __test__ = False  # PyTest is confused by the classname

    class Meta:
        model = TestClass

    repo = factory.SubFactory(RepositoryFactory)


class TestMethodFactory(factory.django.DjangoModelFactory):
    __test__ = False  # PyTest is confused by the classname

    class Meta:
        model = TestMethod

    testclass = factory.SubFactory(TestClassFactory)


class TestResultFactory(factory.django.DjangoModelFactory):
    __test__ = False  # PyTest is confused by the classname

    class Meta:
        model = TestResult

    build_flow = factory.SubFactory(BuildFlowFactory)
    method = factory.SubFactory(TestMethodFactory)


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User
        django_get_or_create = ("username",)

    email = factory.Sequence("user_{}@example.com".format)
    username = factory.Sequence("user_{}@example.com".format)
    password = factory.PostGenerationMethodCall("set_password", "foobar")
    # socialaccount_set = factory.RelatedFactory(SocialAccountFactory, "user")


class StaffSuperuserFactory(UserFactory):
    is_staff = True
    is_superuser = True


def make_user_and_client():
    password = "12345"
    user = StaffSuperuserFactory()
    client = APIClient()
    client.force_authenticate(user)
    response = client.get("/api/")
    if response.status_code == 400 and "DisallowedHost" in str(response.content):
        print("**** YOU MAY NEED TO ADD AN ALLOWED_HOSTS TO YOUR TEST.PY")
        raise (Exception(response))

    assert response.status_code == 200, response.content
    return client, user


def testapi_url(**kwargs):
    params = urlencode(kwargs, True)
    print(params)
    return r"/api/testmethod_perf/?" + params


class TestTestMethodPerfRESTAPI(APITestCase):
    """Test the testmethodperf REST API"""

    @classmethod
    def setUpClass(cls):
        cls.client, cls.user = make_user_and_client()
        super().setUpClass()
        t1 = TestResultFactory(
            method__name="Foo", duration=10, build_flow__tests_total=1
        )
        TestResultFactory(duration=2, build_flow__tests_total=1, method=t1.method)
        TestResultFactory(method__name="Bar", duration=3, build_flow__tests_total=1)
        TestResultFactory(method__name="Bar", duration=5, build_flow__tests_total=1)

    def setUp(self):
        self.client.force_authenticate(self.user)

    @staticmethod
    def find_by_methodname(objs, methodname):
        return next(
            (x for x in objs["results"] if x["method_name"] == methodname), None
        )

    def stats_test_helper(self, stat):
        response = self.client.get(testapi_url(include_fields=stat))
        self.assertEqual(response.status_code, 200)
        return response.json()

    def identical_tests_helper(self, method_name, count, **fields):
        t1 = TestResultFactory(
            build_flow__tests_total=1, method__name=method_name, **fields
        )
        for i in range(count - 1):
            TestResultFactory(**fields, build_flow__tests_total=1, method=t1.method)

    def test_counting(self):
        """Test counting of method invocations"""
        objs = self.stats_test_helper("count")
        print(objs)
        self.assertEqual(self.find_by_methodname(objs, "Foo")["count"], 2)
        self.assertEqual(self.find_by_methodname(objs, "Bar")["count"], 2)

    def test_averaging(self):
        """Test averaging of methods"""
        objs = self.stats_test_helper("duration_average")
        print(objs)

        self.assertEqual(self.find_by_methodname(objs, "Foo")["duration_average"], 6)
        self.assertEqual(self.find_by_methodname(objs, "Bar")["duration_average"], 4)

    def test_all_included_fields(self):
        includable_fields = [
            "duration_average",
            "duration_slow",
            "duration_fast",
            "duration_stddev",
            "duration_coefficient_var",
            "cpu_usage_average",
            "cpu_usage_low",
            "cpu_usage_high",
            "count",
            "failures",
            "assertion_failures",
            "DML_failures",
            "Other_failures",
            "success_percentage",
        ]

        def test_fields(fields):
            response = self.client.get(testapi_url(include_fields=fields))
            self.assertEqual(response.status_code, 200)
            rows = response.json()["results"]
            for field in fields:
                for row in rows:
                    self.assertIn(field, row.keys())

        random.seed("xyzzy")
        for i in range(10):
            field = random.sample(includable_fields, 1)
            test_fields(field)

        for i in range(10):
            field1, field2 = random.sample(includable_fields, 2)
            test_fields([field1, field2])

        for i in range(10):
            field1, field2, field3 = random.sample(includable_fields, 3)
            test_fields([field1, field2, field3])

    def test_duration_slow(self):
        """Test counting high durations"""

        self.identical_tests_helper(method_name="Foo", count=20, duration=10)
        _outlier = TestResultFactory(method__name="Foo", duration=11)  # noqa
        response = self.client.get(
            testapi_url(include_fields=["duration_slow", "count"])
        )
        self.assertEqual(response.status_code, 200)
        objs = response.json()
        print(objs)

        self.assertEqual(self.find_by_methodname(objs, "Foo")["duration_slow"], 10)

    def test_duration_fast(self):
        """Test counting high durations"""

        self.identical_tests_helper(method_name="Foo", count=20, duration=2)
        _outlier = TestResultFactory(method__name="Foo", duration=1)  # noqa
        response = self.client.get(
            testapi_url(include_fields=["duration_slow", "count"])
        )
        self.assertEqual(response.status_code, 200)
        objs = response.json()
        print(objs)

        self.assertEqual(self.find_by_methodname(objs, "Foo")["duration_slow"], 2)

    def test_count_failures(self):
        """Test counting failed tests"""
        self.identical_tests_helper(
            method_name="FailingTest", duration=5, count=15, outcome="Fail"
        )
        self.identical_tests_helper(
            method_name="FailingTest", duration=5, count=10, outcome="Pass"
        )
        response = self.client.get(
            testapi_url(include_fields=["failures", "success_percentage"])
        )
        self.assertEqual(response.status_code, 200)
        objs = response.json()
        print(objs)

        self.assertEqual(self.find_by_methodname(objs, "FailingTest")["failures"], 15)
        self.assertEqual(
            self.find_by_methodname(objs, "FailingTest")["success_percentage"], 10 / 25
        )

    def xyzzy_test_split_by_repo(self):
        """Test counting failed tests"""
        self.identical_tests_helper(
            method_name="HedaTest",
            duration=5,
            count=15,
            build_flow__build__repo__name="HEDA",
        )
        self.identical_tests_helper(
            method_name="NPSPTest",
            duration=5,
            count=20,
            build_flow__build__repo__name="Cumulus",
        )
        response = self.client.get(testapi_url(include_fields="count", group_by="repo"))
        self.assertEqual(response.status_code, 200)
        objs = response.json()
        print(objs)

        self.assertEqual(self.find_by_methodname(objs, "HedaTest")["count"], 15)
        self.assertEqual(self.find_by_methodname(objs, "HedaTest")["repo"], "HEDA")
        self.assertEqual(self.find_by_methodname(objs, "NPSPTest")["count"], 20)
        self.assertEqual(self.find_by_methodname(objs, "NPSPTest")["repo"], "Cumulus")

    def xyzzy_test_split_by_repo_and_flow(self):
        """Test counting failed tests"""
        self.identical_tests_helper(
            method_name="HedaTest",
            duration=5,
            count=15,
            build_flow__build__repo__name="HEDA",
            build_flow__flow="A_HEDA_Flow",
        )
        self.identical_tests_helper(
            method_name="NPSPTest",
            duration=5,
            count=20,
            build_flow__build__repo__name="Cumulus",
            build_flow__flow="A_Cumulus_Flow",
        )
        response = self.client.get(
            testapi_url(include_fields="count", group_by=["repo", "flow"])
        )
        self.assertEqual(response.status_code, 200)
        objs = response.json()
        print(objs)

        self.assertEqual(self.find_by_methodname(objs, "HedaTest")["count"], 15)
        self.assertEqual(self.find_by_methodname(objs, "HedaTest")["repo"], "HEDA")
        self.assertEqual(
            self.find_by_methodname(objs, "HedaTest")["flow"], "A_HEDA_Flow"
        )
        self.assertEqual(self.find_by_methodname(objs, "NPSPTest")["count"], 20)
        self.assertEqual(self.find_by_methodname(objs, "NPSPTest")["repo"], "Cumulus")
        self.assertEqual(
            self.find_by_methodname(objs, "NPSPTest")["flow"], "A_Cumulus_Flow"
        )

    def xyzzy_test_merge_by_flow(self):
        """Test counting failed tests"""
        self.identical_tests_helper(
            method_name="HedaTest",
            duration=5,
            count=15,
            build_flow__build__repo__name="HEDA",
            build_flow__flow="A_HEDA_Flow",
        )
        self.identical_tests_helper(
            method_name="NPSPTest",
            duration=5,
            count=20,
            build_flow__build__repo__name="Cumulus",
            build_flow__flow="A_Cumulus_Flow",
        )
        self.identical_tests_helper(
            method_name="HedaTest",
            duration=5,
            count=15,
            build_flow__build__repo__name="HEDA",
            build_flow__flow="A_Cumulus_Flow",
        )
        self.identical_tests_helper(
            method_name="NPSPTest",
            duration=5,
            count=20,
            build_flow__build__repo__name="Cumulus",
            build_flow__flow="A_HEDA_Flow",
        )

        response = self.client.get(
            r"/api/testmethod_perf/?include_fields=count&group_by=repo&group_by=flow"
        )
        self.assertEqual(response.status_code, 200)
        objs = response.json()
        print(objs)

        self.assertEqual(self.find_by_methodname(objs, "HedaTest")["count"], 25)
        self.assertEqual(
            self.find_by_methodname(objs, "HedaTest")["flow"], "A_HEDA_Flow"
        )
        self.assertEqual(self.find_by_methodname(objs, "NPSPTest")["count"], 20)
        self.assertEqual(
            self.find_by_methodname(objs, "NPSPTest")["flow"], "A_Cumulus_Flow"
        )
