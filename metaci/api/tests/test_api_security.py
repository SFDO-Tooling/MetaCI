import json

from guardian.shortcuts import assign_perm

from metaci.conftest import (
    StaffSuperuserFactory,
    UserFactory,
    RepositoryFactory,
    BranchFactory,
    PlanFactory,
    BuildFactory,
    BuildFlowFactory,
    PlanRepositoryFactory,
    TestResultFactory,
)

from metaci.api import urls

from metaci.plan.models import PlanRepository

from rest_framework.test import APIClient, APITestCase

from .test_testmethod_perf import _TestingHelpers

from config.settings import common


class TestAPISecurity(APITestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        p1 = PlanFactory(name="Plan1")
        p2 = PlanFactory(name="Plan2")
        r1 = RepositoryFactory(name="PublicRepo")
        r2 = RepositoryFactory(name="PrivateRepo")
        PlanRepositoryFactory(plan=p1, repo=r1)
        pr2 = PlanRepositoryFactory(plan=p2, repo=r2)
        BranchFactory(name="Branch1", repo=r1)
        BranchFactory(name="Branch2", repo=r2)
        private_build = BuildFactory(repo=r2, plan=p2, planrepo=pr2)
        private_bff = BuildFlowFactory(build=private_build)
        public_build = BuildFactory(repo=r2, plan=p2, planrepo=pr2)
        public_bff = BuildFlowFactory(build=public_build)
        BuildFlowFactory(flow="Flow2")
        TestResultFactory(build_flow=private_bff)
        TestResultFactory(build_flow=private_bff)
        TestResultFactory(build_flow=public_bff)
        TestResultFactory(build_flow=public_bff)

    @classmethod
    def make_user_and_client(cls, user=None):
        user = user or UserFactory()
        client = APIClient()
        assert client.login(username=user.username, password="foobar")
        return client, user

    # more predictable than full-on inheritance
    debugmsg = _TestingHelpers.debugmsg

    def setUp(self):
        self.client = None  # Let's create each user/client explicitly

    def test_api_schema_protection_normal_user(self):
        client, user = self.make_user_and_client(UserFactory())
        response = client.get("/api/")
        self.debugmsg(response)
        self.assertEqual(response.status_code, 403)

    def test_superuser_access(self):
        superuser = StaffSuperuserFactory()
        client, u = self.make_user_and_client(superuser)
        assert superuser == u
        assert client.login(username=u.username, password="foobar")
        assert client.get("/api/").status_code == 200
        assert client.get("/api/branches/").status_code == 200

    def test_public_access(self):
        client, user = self.make_user_and_client(UserFactory())
        response = client.get("/api/testmethod_perf_UI/")
        self.debugmsg(response)
        self.assertEqual(response.status_code, 200)

    def test_api_methods_IP_view_protection_normal_user(self):
        client, user = self.make_user_and_client()
        superclient, superduper = self.make_user_and_client(StaffSuperuserFactory())

        ip = common.ipv4_networks
        BAD_ADDR = "192.250.0.8"
        GOOD_ADDR = "192.168.0.8"

        all_apis = urls.router.get_urls()

        for route in all_apis:
            pattern = route.pattern.regex.pattern
            is_simple = "(" not in pattern
            if is_simple:
                callable_url = pattern.strip("^$")

                def get(client, addr):
                    self.debugmsg("/api/" + callable_url, addr)
                    return client.get(
                        "/api/" + callable_url, REMOTE_ADDR=addr
                    ).status_code

                is_public = callable_url in [
                    "testmethod_perf_UI/",
                    "testmethod_perf/",
                    "testmethod_results/",
                ]
                if is_public:
                    # IP address and user role don't matter for public URL
                    self.assertEqual(get(client, BAD_ADDR), 200)
                else:
                    with self.settings(ADMIN_API_ALLOWED_SUBNETS=ip("192.168.0.0/16")):
                        # IP matters even for superusers
                        self.assertEqual(get(superclient, BAD_ADDR), 403)
                        # IP matters for normal users
                        self.assertEqual(get(client, BAD_ADDR), 403)

                    with self.settings(ADMIN_API_ALLOWED_SUBNETS=ip("192.168.0.0/16")):
                        # private URL, good IP and superuser permissions = success
                        self.assertEqual(get(superclient, GOOD_ADDR), 200)
                        # private URL, good IP and poor permissions = failure
                        self.assertEqual(get(client, GOOD_ADDR), 403)

    def test_api_schema_superuser(self):
        client, user = self.make_user_and_client(StaffSuperuserFactory())
        response = client.get("/api/")
        self.debugmsg(response)
        self.assertEqual(response.status_code, 200)
        self.assertIn("application/json", response["content-type"])
        self.assertIn(bytes("/api/", "ascii"), response.content)

    def test_object_level_permissions_public_repo(self):
        client, user = self.make_user_and_client()
        response = client.get("/api/testmethod_perf/")
        js = json.loads(response.content)
        assert "count" in js, js
        self.assertEquals(js["count"], 0)

    # todo: combine this test with the one below somehow
    def test_object_level_permission_denial_private_repo(self):
        client, user = self.make_user_and_client()
        r1 = PlanRepository.objects.filter(repo__name="PrivateRepo")
        assert len(r1) == 1
        # print(assign_perm("plan.view_stats", user, r1[0]))
        response = client.get("/api/testmethod_perf/")
        js = json.loads(response.content)
        assert "count" in js, js
        self.assertEqual(js["count"], 0)

    def test_object_level_permission_success_private_repo(self):
        client, user = self.make_user_and_client()
        r1 = PlanRepository.objects.filter(repo__name="PrivateRepo")
        assert len(r1) == 1
        print(assign_perm("plan.view_stats", user, r1[0]))
        response = client.get("/api/testmethod_perf/")
        js = json.loads(response.content)
        self.assertGreater(js["count"], 0)

    def test_superuser_success_private_repo(self):
        client, superuser = self.make_user_and_client(StaffSuperuserFactory())
        response = client.get("/api/testmethod_perf/")
        js = json.loads(response.content)
        assert "count" in js, js
        self.assertGreater(js["count"], 2)
