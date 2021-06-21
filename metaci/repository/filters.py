import rest_framework_filters as filters

from metaci.repository.models import Branch, Repository


class RepositoryRelatedFilter(filters.FilterSet):
    class Meta:
        model = Repository
        fields = ["id", "name", "owner", "url", "github_id"]


class RepositoryFilter(RepositoryRelatedFilter):
    pass


class BranchRelatedFilter(filters.FilterSet):
    repo = filters.RelatedFilter(
        RepositoryRelatedFilter, name="repo", queryset=Repository.objects.all()
    )

    class Meta:
        model = Branch
        fields = ["id", "name"]


class BranchFilter(BranchRelatedFilter):
    pass
