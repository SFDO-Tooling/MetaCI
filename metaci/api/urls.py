from django.urls import re_path
from rest_framework.routers import DefaultRouter
from rest_framework.schemas import get_schema_view

from metaci.api.views.build import BuildFlowViewSet, BuildViewSet, RebuildViewSet
from metaci.api.views.cumulusci import (
    OrgViewSet,
    ScratchOrgInstanceViewSet,
    ServiceViewSet,
)
from metaci.api.views.plan import PlanRepositoryViewSet, PlanViewSet
from metaci.api.views.repository import BranchViewSet, RepositoryViewSet
from metaci.api.views.robot import RobotTestResultViewSet

router = DefaultRouter()
router.register(r"branches", BranchViewSet, basename="branch")
router.register(r"builds", BuildViewSet, basename="build")
router.register(r"build_flows", BuildFlowViewSet, basename="build_flow")
router.register(r"orgs", OrgViewSet, basename="org")
router.register(r"plans", PlanViewSet, basename="plan")
router.register(r"plan_repos", PlanRepositoryViewSet, basename="plan_repo")
router.register(r"rebuilds", RebuildViewSet, basename="rebuild")
router.register(r"repos", RepositoryViewSet, basename="repo")
router.register(r"scratch_orgs", ScratchOrgInstanceViewSet, basename="scratch_org")
router.register(r"services", ServiceViewSet, basename="service")
router.register(r"robot", RobotTestResultViewSet, basename="robot")

urlpatterns = router.urls

schema_view = get_schema_view(title="MetaCI API")
urlpatterns += (re_path(r"^schema/$", schema_view),)
