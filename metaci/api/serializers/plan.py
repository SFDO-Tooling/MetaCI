from rest_framework import serializers

from metaci.api.serializers.repository import RepositorySerializer
from metaci.plan.models import Plan, PlanRepository
from metaci.repository.models import Repository


class PlanSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Plan
        fields = (
            "id",
            "active",
            "commit_status_regex",
            "context",
            "description",
            "flows",
            "name",
            "org",
            "role",
            "regex",
            "trigger",
        )


class PlanRepositorySerializer(serializers.HyperlinkedModelSerializer):
    plan = PlanSerializer(read_only=True)
    plan_id = serializers.PrimaryKeyRelatedField(
        queryset=Plan.objects.all(), source="plan", write_only=True
    )
    repo = RepositorySerializer(read_only=True)
    repo_id = serializers.PrimaryKeyRelatedField(
        queryset=Repository.objects.all(), source="repo", write_only=True
    )

    class Meta:
        model = PlanRepository
        fields = ("id", "plan", "plan_id", "repo", "repo_id")
