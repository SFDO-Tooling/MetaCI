import rest_framework_filters as filters
from mrbelvedereci.cumulusci.models import Org
from mrbelvedereci.cumulusci.models import ScratchOrgInstance
from mrbelvedereci.cumulusci.models import Service
from mrbelvedereci.repository.filters import RepositoryRelatedFilter
from mrbelvedereci.repository.models import Repository

class OrgRelatedFilter(filters.FilterSet):
    repo = filters.RelatedFilter(
        RepositoryRelatedFilter,
        name='repo',
        queryset=Repository.objects.all()
    )
    class Meta:
        model = Org
        fields = {
            'json': ['icontains'],
            'name': ['exact'],
            'scratch': ['exact'],
        }

class OrgFilter(OrgRelatedFilter):
    pass

class ScratchOrgInstanceRelatedFilter(filters.FilterSet):
    org = filters.RelatedFilter(
        OrgRelatedFilter,
        name='org',
        queryset=Repository.objects.all()
    )
    class Meta:
        model = ScratchOrgInstance
        fields = {
            'build': ['exact'],
            'deleted': ['exact'],
            'sf_org_id': ['exact'],
            'time_created': ['gt','lt'],
            'time_deleted': ['gt','lt'],
            'username': ['exact'],
        }

class ScratchOrgInstanceFilter(ScratchOrgInstanceRelatedFilter):
    pass

class ServiceRelatedFilter(filters.FilterSet):
    class Meta:
        model = Org
        fields = {
            'json': ['icontains'],
            'name': ['exact'],
        }

class ServiceFilter(OrgRelatedFilter):
    pass
