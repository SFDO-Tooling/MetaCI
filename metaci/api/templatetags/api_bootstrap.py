import json

from django import template
from django.utils.html import escape

from ..serializers.user import FullUserSerializer

register = template.Library()


# Based upon https://github.com/SFDO-Tooling/sfdo-template/blob/9362a1e18864282fcd9d0571f66a2845200b9ef1/%7B%7Bcookiecutter.project_slug%7D%7D/src/index.html
@register.filter
def serialize(user):
    return escape(json.dumps(FullUserSerializer(user).data))
