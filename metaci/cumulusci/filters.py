import rest_framework_filters as filters
from metaci.cumulusci.models import Org
from metaci.cumulusci.models import ScratchOrgInstance
from metaci.cumulusci.models import Service
from metaci.repository.filters import RepositoryRelatedFilter
from metaci.repository.models import Repository

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
            'org_type': ['exact'],
            'org_id': ['iexact']
        }

class OrgFilter(OrgRelatedFilter):
    pass

class RegisteredOrgFilter(OrgRelatedFilter):
    class Meta:
        model = Org
        fields = {
            'name': ['exact'],
            'org_type': ['exact'],
            'org_id': ['iexact'],
            'release_cycle': ['exact'],
        } 

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
