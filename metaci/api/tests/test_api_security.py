from metaci.conftest import (
    StaffSuperuserFactory,
    UserFactory,
    RepositoryFactory,
    BranchFactory,
    PlanFactory,
    BuildFlowFactory,
)

from metaci.api import urls

from rest_framework.test import APIClient, APITestCase

from .test_testmethod_perf import _TestingHelpers

from config.settings import common


class TestAPISecurity(APITestCase):
    @classmethod
    def setUpClass(cls):
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
        client.force_authenticate(user)
        response = client.get("/api/")
        self.debugmsg(response)
        self.assertEqual(response.status_code, 403)

    def test_superuser_access(self):
        superuser = StaffSuperuserFactory()
        client, u = self.make_user_and_client(superuser)
        assert superuser == u
        client.force_authenticate(user=superuser)
        assert client.login(username=u.username, password="foobar")
        assert client.get("/api/").status_code == 200
        assert client.get("/api/branches/").status_code == 200

    def test_public_access(self):
        client, user = self.make_user_and_client(UserFactory())
        client.force_authenticate(user)
        response = client.get("/api/testmethod_perf_UI/")
        self.debugmsg(response)
        self.assertEqual(response.status_code, 200)

    def test_api_methods_IP_view_protection_normal_user(self):
        client, user = self.make_user_and_client()
        superclient, superduper = self.make_user_and_client(StaffSuperuserFactory())
        superclient.force_authenticate(user=superduper)

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

                is_public = callable_url == "testmethod_perf_UI/"
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
