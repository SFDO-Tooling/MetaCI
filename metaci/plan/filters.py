import rest_framework_filters as filters

from metaci.plan.models import Plan, PlanRepository
from metaci.repository.filters import RepositoryRelatedFilter
from metaci.repository.models import Repository


class PlanRelatedFilter(filters.FilterSet):
    class Meta:
        model = Plan
        fields = [
            "active",
            "context",
            "flows",
            "id",
            "name",
            "org",
            "regex",
            "role",
            "trigger",
        ]


class PlanFilter(PlanRelatedFilter):
    pass


class PlanRepositoryRelatedFilter(filters.FilterSet):
    plan = filters.RelatedFilter(
        PlanRelatedFilter, name="plan", queryset=Plan.objects.all()
    )
    repo = filters.RelatedFilter(
        RepositoryRelatedFilter, name="repo", queryset=Repository.objects.all()
    )

    class Meta:
        model = PlanRepository
        fields = ["id"]


class PlanRepositoryFilter(PlanRepositoryRelatedFilter):
    pass
