from django.core.management.base import BaseCommand, CommandError
from metaci.users.models import User
from rest_framework.authtoken.models import Token


class Command(BaseCommand):
    help = "Returns the API token for a given username.  If one does not exist, a token is first created."

    def add_arguments(self, parser):
        parser.add_argument("username", type=str)

    def handle(self, *args, **options):
        try:
            user = User.objects.get(username=options["username"])
        except User.DoesNotExist:
            raise CommandError("User named does not exist".format(options["username"]))
        token, created = Token.objects.get_or_create(user=user)
        self.stdout.write("Token: {}".format(token.key))
