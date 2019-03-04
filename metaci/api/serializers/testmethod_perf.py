from rest_framework import serializers



class TestMethodPerfSerializer(serializers.Serializer):
    method_name = serializers.CharField()
    count = serializers.IntegerField()
    avg = serializers.FloatField()
    repo = serializers.CharField()
    plan = serializers.CharField()
    flow = serializers.CharField()
    class Meta:
        fields = ("method_name", "count", "avg", "repo")
