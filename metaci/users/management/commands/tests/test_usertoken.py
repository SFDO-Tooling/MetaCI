import pytest
from unittest.mock import Mock

from django.core.management.base import CommandError

from metaci.users.models import User
from rest_framework.authtoken.models import Token
from metaci.users.management.commands.usertoken import Command


@pytest.mark.django_db
class TestUserToken:
    command = Command()

    def test_add_arguments(self, data, user):
        parser = Mock(add_argument=Mock())
        self.command.add_arguments(parser)
        parser.add_argument.assert_called_once_with("username", type=str)

    def test_handle__user_exists(self, data, user, capsys):
        num_tokens = Token.objects.all().count()
        self.command.handle("arg1", "arg2", username=user.username)
        stdout, stderr = capsys.readouterr()
        assert Token.objects.all().count() == num_tokens + 1

    def test_handle__user_does_not_exist(self, data):
        with pytest.raises(CommandError):
            self.command.handle(username="does not exist")

