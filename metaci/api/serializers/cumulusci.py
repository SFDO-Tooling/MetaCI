from rest_framework import serializers

from metaci.api.serializers.repository import RepositorySerializer
from metaci.cumulusci.models import Org, ScratchOrgInstance, Service
from metaci.repository.models import Repository


class OrgSerializer(serializers.HyperlinkedModelSerializer):
    repo = RepositorySerializer(read_only=True)
    repo_id = serializers.PrimaryKeyRelatedField(
        queryset=Repository.objects.all(), source="repo", write_only=True
    )

    class Meta:
        model = Org
        fields = ("id", "json", "name", "repo", "repo_id", "scratch")


class ScratchOrgInstanceSerializer(serializers.HyperlinkedModelSerializer):
    org = OrgSerializer(read_only=True)
    org_id = serializers.PrimaryKeyRelatedField(
        queryset=Org.objects.all(), source="org", write_only=True
    )

    class Meta:
        model = ScratchOrgInstance
        fields = (
            "id",
            "build",
            "deleted",
            "org",
            "org_id",
            "sf_org_id",
            "time_created",
            "time_deleted",
            "username",
        )


class ServiceSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Service
        fields = ("id", "name", "json")
