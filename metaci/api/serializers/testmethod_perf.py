from rest_framework import serializers


class TestMethodPerfSerializer(serializers.Serializer):
    method_name = serializers.CharField()
    count = serializers.IntegerField()
    avg = serializers.FloatField()
    repo = serializers.CharField(required=False, default=None)
    plan = serializers.CharField(required=False, default=None)
    flow = serializers.CharField(required=False, default=None)
    branch = serializers.CharField(required=False, default=None)
