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
    # At the moment, the only dates we have available are from the build
    # itself. It would be nice if this was the actual datetime of the
    # test rather than the build.
    date = serializers.DateTimeField(
        source="build_flow.time_end", read_only=True, format="%Y-%m-%d %H:%M:%S"
    )

    class Meta:
        model = TestResult
        fields = (
            "id",
            "outcome",
            "date",
            "duration",
            "repo_name",
            "branch_name",
            "source_file",
            "test_name",
            "robot_tags",
            "robot_keyword",
            "message",
        )
