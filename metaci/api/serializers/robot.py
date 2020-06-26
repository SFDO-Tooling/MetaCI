from rest_framework import serializers
from metaci.testresults.models import TestResult


class RobotTestResultSerializer(serializers.ModelSerializer):
    test_name = serializers.ReadOnlyField(source="method.name")
    repo_name = serializers.CharField(
        source="build_flow.build.repo.name", read_only=True,
    )
    branch_name = serializers.CharField(
        source="build_flow.build.branch.name", read_only=True,
    )

    class Meta:
        model = TestResult
        fields = (
            "id",
            "repo_name",
            "branch_name",
            "outcome",
            "source_file",
            "test_name",
            "message",
            "robot_keyword",
        )
