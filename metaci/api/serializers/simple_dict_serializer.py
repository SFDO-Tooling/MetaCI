from rest_framework import serializers


class SimpleDictSerializer(serializers.Serializer):
    """A serializer for data that is already ready for JSON"""

    def to_representation(self, instance):
        """Takes in instances that are more or less dicts and simply returns them"""
        return instance
