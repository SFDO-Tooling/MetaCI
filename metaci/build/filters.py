import rest_framework_filters as filters
from metaci.build.models import Build
from metaci.build.models import BuildFlow
from metaci.build.models import Rebuild
from metaci.cumulusci.filters import OrgRelatedFilter
from metaci.cumulusci.filters import ScratchOrgInstanceRelatedFilter
from metaci.cumulusci.models import Org
from metaci.cumulusci.models import ScratchOrgInstance
from metaci.plan.filters import PlanRelatedFilter
from metaci.plan.models import Plan
from metaci.repository.filters import BranchRelatedFilter
from metaci.repository.filters import RepositoryRelatedFilter
from metaci.repository.models import Branch
from metaci.repository.models import Repository

class BuildRelatedFilter(filters.FilterSet):
    branch = filters.RelatedFilter(
        BranchRelatedFilter,
        name='branch',
        queryset=Branch.objects.all()
    )
    org = filters.RelatedFilter(
        OrgRelatedFilter,
        name='org',
        queryset=Org.ci_orgs.all()
    )
    plan = filters.RelatedFilter(
        PlanRelatedFilter,
        name='plan',
        queryset=Plan.objects.all()
    )
    repo = filters.RelatedFilter(
        RepositoryRelatedFilter,
        name='repo',
        queryset=Repository.objects.all()
    )

    class Meta:
        model = Build
        fields = {
            'commit': ['exact'],
            'status': ['exact'],
            'time_queue': ['gt','lt'],
            'time_start': ['gt','lt'],
            'time_end': ['gt','lt'],
        }

class BuildFilter(BuildRelatedFilter):
    pass

class RebuildRelatedFilter(filters.FilterSet):
    build = filters.RelatedFilter(
        BuildRelatedFilter,
        name='build',
        queryset=Build.objects.all()
    )
    class Meta:
        model = Rebuild
        fields = {
            'status': ['exact'],
            'time_queue': ['gt','lt'],
            'time_start': ['gt','lt'],
            'time_end': ['gt','lt'],
        }

class RebuildFilter(RebuildRelatedFilter):
    pass


class BuildFlowRelatedFilter(filters.FilterSet):
    build = filters.RelatedFilter(
        BuildRelatedFilter,
        name='build',
        queryset=Build.objects.all()
    )
    rebuild = filters.RelatedFilter(
        RebuildRelatedFilter,
        name='build',
        queryset=Rebuild.objects.all()
    )

    class Meta:
        model = BuildFlow
        fields = {
            'status': ['exact'],
            'time_queue': ['gt','lt'],
            'time_start': ['gt','lt'],
            'time_end': ['gt','lt'],
        }
   
class BuildFlowFilter(BuildFlowRelatedFilter):
    pass 
