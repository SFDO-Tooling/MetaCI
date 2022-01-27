import json

import pytest
from django.contrib.auth.models import Group
from guardian.shortcuts import assign_perm
from rest_framework.test import APIClient, APITestCase

from config.settings import base
from metaci.api import urls
from metaci.conftest import (
    BranchFactory,
    BuildFactory,
    BuildFlowFactory,
    PlanFactory,
    PlanRepositoryFactory,
    RepositoryFactory,
    StaffSuperuserFactory,
    TestResultFactory,
    UserFactory,
)
from metaci.plan.models import PlanRepository


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

    def setUp(self):
        self.client = None  # Let's create each user/client explicitly

    def test_api_schema_protection_normal_user(self):
        client, user = self.make_user_and_client(UserFactory())
        response = client.get("/api/")
        self.assertEqual(response.status_code, 403)

    def test_superuser_access(self):
        superuser = StaffSuperuserFactory()
        client, u = self.make_user_and_client(superuser)
        assert superuser == u
        assert client.login(username=u.username, password="foobar")
        assert client.get("/api/").status_code == 200
        assert client.get("/api/branches/").status_code == 200

    def test_api_methods_IP_view_protection_normal_user(self):
        client, user = self.make_user_and_client()
        superclient, superduper = self.make_user_and_client(StaffSuperuserFactory())

        ip = base.ipv4_networks
        BAD_ADDR = "192.250.0.8"
        GOOD_ADDR = "192.168.0.8"

        all_apis = urls.router.get_urls()

        for route in all_apis:
            pattern = route.pattern.regex.pattern
            is_simple = "(" not in pattern
            if is_simple:
                callable_url = pattern.strip("^$")

                def get(client, addr):
                    return client.get(
                        "/api/" + callable_url, REMOTE_ADDR=addr
                    ).status_code

                is_public = callable_url in [
                    "testmethod_results/",
                    "robot/",
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
        self.assertEqual(response.status_code, 200)
        self.assertIn("application/json", response["content-type"])
        self.assertIn(bytes("/api/", "ascii"), response.content)
