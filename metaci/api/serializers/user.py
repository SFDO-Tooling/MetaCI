from django.contrib.auth import get_user_model
from rest_framework import serializers

User = get_user_model()


# Based upon https://github.com/SFDO-Tooling/sfdo-template/blob/fa7bdd749dc8970947913f4a38e9fb06f399dd1b/%7B%7Bcookiecutter.project_slug%7D%7D/%7B%7Bcookiecutter.project_slug%7D%7D/api/serializers.py
class FullUserSerializer(serializers.ModelSerializer):
    id = serializers.CharField(read_only=True)

    class Meta:
        model = User
        fields = ("id", "username", "email", "is_staff")
