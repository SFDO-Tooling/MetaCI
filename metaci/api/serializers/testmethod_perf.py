from rest_framework import serializers
from collections import OrderedDict


class NonNullModelSerializer(serializers.Serializer):
    def to_representation(self, instance):
        result = super(NonNullModelSerializer, self).to_representation(instance)
        return OrderedDict([(key, result[key]) for key in result if result[key] is not None])

class TestMethodPerfSerializer(NonNullModelSerializer):
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
