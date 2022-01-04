import rest_framework_filters as filters
from metaci.build.models import Build
from metaci.build.models import BuildFlow
from metaci.build.models import Rebuild
from metaci.cumulusci.filters import OrgRelatedFilter
from metaci.cumulusci.models import Org
from metaci.plan.filters import PlanRelatedFilter
from metaci.plan.models import Plan
from metaci.repository.filters import BranchRelatedFilter
from metaci.repository.filters import RepositoryRelatedFilter
from metaci.repository.models import Branch
from metaci.repository.models import Repository


class BuildRelatedFilter(filters.FilterSet):
    branch = filters.RelatedFilter(
        BranchRelatedFilter, field_name="branch", queryset=Branch.objects.all()
    )
    org = filters.RelatedFilter(
        OrgRelatedFilter, field_name="org", queryset=Org.objects.all()
    )
    plan = filters.RelatedFilter(
        PlanRelatedFilter, field_name="plan", queryset=Plan.objects.all()
    )
    repo = filters.RelatedFilter(
        RepositoryRelatedFilter, field_name="repo", queryset=Repository.objects.all()
    )

    class Meta:
        model = Build
        fields = {
            "commit": ["exact"],
            "status": ["exact"],
            "time_queue": ["gt", "lt"],
            "time_start": ["gt", "lt"],
            "time_end": ["gt", "lt"],
        }


class BuildFilter(BuildRelatedFilter):
    pass


class RebuildRelatedFilter(filters.FilterSet):
    build = filters.RelatedFilter(
        BuildRelatedFilter, name="build", queryset=Build.objects.all()
    )

    class Meta:
        model = Rebuild
        fields = {
            "status": ["exact"],
            "time_queue": ["gt", "lt"],
            "time_start": ["gt", "lt"],
            "time_end": ["gt", "lt"],
        }


class RebuildFilter(RebuildRelatedFilter):
    pass


class BuildFlowRelatedFilter(filters.FilterSet):
    build = filters.RelatedFilter(
        BuildRelatedFilter, field_name="build", queryset=Build.objects.all()
    )
    rebuild = filters.RelatedFilter(
        RebuildRelatedFilter, field_name="build", queryset=Rebuild.objects.all()
    )

    class Meta:
        model = BuildFlow
        fields = {
            "status": ["exact"],
            "time_queue": ["gt", "lt"],
            "time_start": ["gt", "lt"],
            "time_end": ["gt", "lt"],
        }


class BuildFlowFilter(BuildFlowRelatedFilter):
    pass
