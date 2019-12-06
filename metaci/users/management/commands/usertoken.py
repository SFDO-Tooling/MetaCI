from django.core.management.base import BaseCommand, CommandError
from rest_framework.authtoken.models import Token

from metaci.users.models import User


class Command(BaseCommand):
    help = "Returns the API token for a given username.  If one does not exist, a token is first created."

    def add_arguments(self, parser):
        parser.add_argument("username", type=str)

    def handle(self, *args, **options):
        try:
            user = User.objects.get(username=options["username"])
        except User.DoesNotExist:
            raise CommandError(f"Username does not exist: {options['username']}")
        token, created = Token.objects.get_or_create(user=user)
        self.stdout.write(f"Token: {token.key}")
