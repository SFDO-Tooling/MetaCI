import rest_framework_filters as filters
from metaci.repository.filters import RepositoryRelatedFilter
from metaci.plan.models import Plan
from metaci.repository.models import Repository

class PlanRelatedFilter(filters.FilterSet):
    repo = filters.RelatedFilter(RepositoryRelatedFilter, name='repo', queryset=Repository.objects.all())
    class Meta:
        model = Plan
        fields = [
            'active',
            'context',
            'flows',
            'id',
            'name',
            'org',
            'public',
            'regex',
            'type',
        ]

class PlanFilter(PlanRelatedFilter):
    pass
