import unittest

import pytest
from django.test import RequestFactory

from ..models import User
from ..views import UserRedirectView, UserUpdateView


@pytest.mark.django_db
class BaseUserTestCase(unittest.TestCase):
    def setUp(self):
        self.user = User(username="testuser")
        self.user.save()
        self.factory = RequestFactory()


class TestUserRedirectView(BaseUserTestCase):
    def test_get_redirect_url(self):
        # Instantiate the view directly. Never do this outside a test!
        view = UserRedirectView()
        # Generate a fake request
        request = self.factory.get("/fake-url")
        # Attach the user to the request
        request.user = self.user
        # Attach the request to the view
        view.request = request
        self.assertEqual(view.get_redirect_url(), "/users/testuser/")


class TestUserUpdateView(BaseUserTestCase):
    def setUp(self):
        # call BaseUserTestCase.setUp()
        super(TestUserUpdateView, self).setUp()
        # Instantiate the view directly. Never do this outside a test!
        self.view = UserUpdateView()
        # Generate a fake request
        request = self.factory.get("/fake-url")
        # Attach the user to the request
        request.user = self.user
        # Attach the request to the view
        self.view.request = request

    def test_get_success_url(self):
        self.assertEqual(self.view.get_success_url(), "/users/testuser/")

    def test_get_object(self):
        # Expect: self.user, as that is the request's user object
        self.assertEqual(self.view.get_object(), self.user)
