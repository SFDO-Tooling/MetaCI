from django.conf.urls import url
from mrbelvedereci.api.views.build import BuildViewSet
from mrbelvedereci.api.views.build import BuildFlowViewSet
from mrbelvedereci.api.views.build import RebuildViewSet
from mrbelvedereci.api.views.cumulusci import OrgViewSet
from mrbelvedereci.api.views.cumulusci import ScratchOrgInstanceViewSet
from mrbelvedereci.api.views.cumulusci import ServiceViewSet
from mrbelvedereci.api.views.plan import PlanViewSet
from mrbelvedereci.api.views.repository import BranchViewSet
from mrbelvedereci.api.views.repository import RepositoryViewSet
from rest_framework.routers import DefaultRouter
from rest_framework.schemas import get_schema_view

router = DefaultRouter()
router.register(r'branches', BranchViewSet, base_name='branch')
router.register(r'builds', BuildViewSet, base_name='build')
router.register(r'build_flows', BuildFlowViewSet, base_name='build_flow')
router.register(r'orgs', OrgViewSet, base_name='org')
router.register(r'plans', PlanViewSet, base_name='plan')
router.register(r'rebuilds', RebuildViewSet, base_name='rebuild')
router.register(r'repos', RepositoryViewSet, base_name='repo')
router.register(r'scratch_orgs', ScratchOrgInstanceViewSet, base_name='scratch_org')
router.register(r'services', ServiceViewSet, base_name='service')
urlpatterns = router.urls

schema_view = get_schema_view(title='MetaCI API')
urlpatterns += (
    url(r'^schema/$', schema_view),
)
