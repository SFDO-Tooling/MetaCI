from rest_framework import serializers
from metaci.testresults.models import TestResult


class RobotTestResultSerializer(serializers.ModelSerializer):
    method = serializers.ReadOnlyField(source="method.name")

    class Meta:
        model = TestResult
        fields = (
            "id",
            "outcome",
            "source_file",
            "method",
            "message",
            "robot_keyword",
        )
