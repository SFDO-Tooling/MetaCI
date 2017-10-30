import rest_framework_filters as filters
from mrbelvedereci.repository.filters import RepositoryRelatedFilter
from mrbelvedereci.plan.models import Plan
from mrbelvedereci.repository.models import Repository

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
