from rest_framework import serializers
from collections import OrderedDict


class NonNullModelSerializer(serializers.Serializer):
    def to_representation(self, instance):
        result = super(NonNullModelSerializer, self).to_representation(instance)
        return OrderedDict(
            [(key, result[key]) for key in result if result[key] is not None]
        )


class TestMethodPerfSerializer(serializers.Serializer):
    def to_representation(self, instance):
        return instance
