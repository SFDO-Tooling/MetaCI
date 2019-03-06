from rest_framework import serializers


class TestMethodPerfSerializer(serializers.Serializer):
    method_name = serializers.CharField()
    count = serializers.IntegerField()
    avg = serializers.FloatField()
    failures = serializers.IntegerField(required=False, default=None)
    assertion_failures = serializers.IntegerField(required=False, default=None)
    DML_failures = serializers.IntegerField(required=False, default=None)
    Other_failures = serializers.IntegerField(required=False, default=None)
    repo = serializers.CharField(required=False, default=None)
    plan = serializers.CharField(required=False, default=None)
    flow = serializers.CharField(required=False, default=None)
    branch = serializers.CharField(required=False, default=None)
