import json

from guardian.shortcuts import assign_perm
from django.contrib.auth.models import Group

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
        public_pr = PlanRepositoryFactory(plan=p1, repo=r1)
        assign_perm("plan.view_builds", Group.objects.get(name="Public"), public_pr)
        pr2 = PlanRepositoryFactory(plan=p2, repo=r2)
        BranchFactory(name="Branch1", repo=r1)
        BranchFactory(name="Branch2", repo=r2)
        private_build = BuildFactory(repo=r2, plan=p2, planrepo=pr2)
        private_bff = BuildFlowFactory(build=private_build)
        public_build = BuildFactory(repo=r2, plan=p2, planrepo=pr2)
        public_bff = BuildFlowFactory(build=public_build)
        BuildFlowFactory(flow="Flow2")
        TestResultFactory(build_flow=private_bff, method__name="Private1")
        TestResultFactory(build_flow=private_bff, method__name="Private2")
        TestResultFactory(build_flow=public_bff, method__name="Public1")
        TestResultFactory(build_flow=public_bff, method__name="Public2")

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

    # not an API test strictly speaking but it depends on the infrastructure
    # for API tests so this is a good place for it until we have more such
    # tests
    def test_login_required_for_testresults_page(self):
        client = APIClient()
        client.logout()

        private = PlanRepository.objects.filter(repo__name="PrivateRepo").first().repo

        response = client.get(f"/repos/{private}/perf")
        self.debugmsg(response)
        self.assertEqual(response.status_code, 404)  # don't acknowledge repo exists

        public = PlanRepository.objects.filter(repo__name="PublicRepo").first().repo
        response = client.get(f"/repos/{public}/perf")
        self.debugmsg(response)
        self.assertEqual(
            response.status_code, 200
        )  # repo exists but you can't see test data on it
        self.assertIn("Please login", response.content.decode("utf-8"))

    # same comment as above
    def test_testresults_page_visible_to_logged_in_users(self):
        client, user = self.make_user_and_client(UserFactory())
        private_planrepo = PlanRepository.objects.filter(
            repo__name="PrivateRepo"
        ).first()
        assign_perm("plan.view_builds", user, private_planrepo)

        response = client.get(f"/repos/{private_planrepo.repo}/perf")
        self.debugmsg(response)
        self.assertEqual(response.status_code, 200)
        self.assertNotIn("Please login", response.content.decode("utf-8"))

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
        self.assertEqual(js["count"], 0)

    def test_object_level_permission_denial_private_repo(self):
        client, user = self.make_user_and_client()
        r1 = PlanRepository.objects.filter(repo__name="PrivateRepo")
        assert len(r1) == 1
        response = client.get("/api/testmethod_perf/")
        js = json.loads(response.content)
        assert "count" in js, js
        self.assertEqual(js["count"], 0)

    def test_object_level_permission_success_private_repo(self):
        client, user = self.make_user_and_client()
        r1 = PlanRepository.objects.filter(repo__name="PrivateRepo")
        assert len(r1) == 1
        assign_perm("plan.view_builds", user, r1[0])
        response = client.get("/api/testmethod_perf/")
        js = json.loads(response.content)
        self.assertGreater(js["count"], 0)

    def test_superuser_success_private_repo(self):
        client, superuser = self.make_user_and_client(StaffSuperuserFactory())
        response = client.get("/api/testmethod_perf/")
        js = json.loads(response.content)
        print(response.content)
        assert "count" in js, js
        self.assertGreater(js["count"], 2)
