import pytest
from django.core.exceptions import PermissionDenied
from django.test import RequestFactory
from guardian.shortcuts import assign_perm

from metaci.testresults import utils


class TestTestResultUtils:
    """Unit tests for testresults.utils.py"""

    req_factory = RequestFactory()

    @pytest.mark.django_db
    def test_find_buildflow__no_user_perms(self, user, data):
        request = self.req_factory.get("/testresults/something")
        request.user = user

        with pytest.raises(PermissionDenied):
            utils.find_buildflow(request, data["build"].id, "random_flow_name")

    @pytest.mark.django_db
    @pytest.mark.skip
    def test_find_buildflow(self, user, data):
        assign_perm("plan.view_builds", user, data["planrepo"])

        request = self.req_factory.get("/testresults/something")
        request.user = user

        # Flow name needs to match name created in data fixture
        build_flow = utils.find_buildflow(request, data["build"].id, "flow_one")
        assert build_flow is data["buildflow"]
