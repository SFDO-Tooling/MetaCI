import unittest


from metaci.users.models import User


class TestUser(unittest.TestCase):
    def setUp(self):
        self.user = User(username="testuser")

    def test__str__(self):
        self.assertEqual(
            self.user.__str__(),
            "testuser",
        )

    def test_get_absolute_url(self):
        self.assertEqual(self.user.get_absolute_url(), "/users/testuser/")
