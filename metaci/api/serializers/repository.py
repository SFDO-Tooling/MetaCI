from rest_framework import serializers

from metaci.repository.models import Branch, Repository


class RepositorySerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Repository
        fields = ("id", "github_id", "name", "owner", "url")


class BranchSerializer(serializers.HyperlinkedModelSerializer):
    repo = RepositorySerializer(read_only=True)
    repo_id = serializers.PrimaryKeyRelatedField(
        queryset=Repository.objects.all(), source="repo", write_only=True
    )

    class Meta:
        model = Branch
        fields = ("id", "name", "repo", "repo_id")
