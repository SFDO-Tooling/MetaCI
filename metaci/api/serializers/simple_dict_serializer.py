from rest_framework import serializers


class SimpleDictSerializer(serializers.Serializer):
    def to_representation(self, instance):
        return instance
