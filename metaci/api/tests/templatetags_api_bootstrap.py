import json

import pytest
from django.utils.html import escape

from ..templatetags.api_bootstrap import serialize


# Based on https://github.com/SFDO-Tooling/sfdo-template/blob/fa7bdd749dc8970947913f4a38e9fb06f399dd1b/%7B%7Bcookiecutter.project_slug%7D%7D/%7B%7Bcookiecutter.project_slug%7D%7D/api/tests/templatetags_api_bootstrap.py
@pytest.mark.django_db
def test_serialize(user_factory):
    user = user_factory(
        email="template_tags@example.com", username="template_tags@example.com"
    )
    actual = serialize(user)
    expected = escape(
        json.dumps(
            {
                "id": str(user.id),
                "username": "template_tags@example.com",
                "email": "template_tags@example.com",
                "is_staff": False,
            }
        )
    )
    assert actual == expected
