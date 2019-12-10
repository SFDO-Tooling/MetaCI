import pytest
from django.test import Client


@pytest.fixture
def client():
    return Client()
