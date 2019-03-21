from django.conf.urls import url
from metaci.api.views.build import BuildViewSet
from metaci.api.views.build import BuildFlowViewSet
from metaci.api.views.build import RebuildViewSet
from metaci.api.views.cumulusci import OrgViewSet
from metaci.api.views.cumulusci import ScratchOrgInstanceViewSet
from metaci.api.views.cumulusci import ServiceViewSet
from metaci.api.views.plan import PlanViewSet
from metaci.api.views.plan import PlanRepositoryViewSet
from metaci.api.views.repository import BranchViewSet
from metaci.api.views.repository import RepositoryViewSet
from metaci.api.views.testmethod_perf import TestMethodPerfListView
from rest_framework.routers import DefaultRouter
from rest_framework.schemas import get_schema_view

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
router.register(r"testmethod_perf", TestMethodPerfListView, basename="testmethod_perf")
urlpatterns = router.urls

schema_view = get_schema_view(title="MetaCI API")
urlpatterns += (url(r"^schema/$", schema_view),)
