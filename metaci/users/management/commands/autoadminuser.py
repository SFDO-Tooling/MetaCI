import os
from django.core.management.base import BaseCommand, CommandError
from metaci.users.models import User


class Command(BaseCommand):
    help = "Auto-creates an admin user with the password from ADMINUSER_PASS env var or an auto generated random password.  If a random pass is generated, it is printed to the terminal.  No password is printed if using the env var."

    def add_arguments(self, parser):
        parser.add_argument("email", type=str)
        parser.add_argument(
            "--user",
            dest="user",
            default="admin",
            help="Use a different username than admin",
        )

    def handle(self, *args, **options):
        try:
            existing = User.objects.get(username=options["user"])
        except User.DoesNotExist:
            existing = False

        if existing:
            raise CommandError("User named {} already exists".format(options["user"]))

        password = os.environ.get("ADMINUSER_PASS")
        if password:
            password_source = "env"
        else:
            password_source = "random"
            password = User.objects.make_random_password()
        password = os.environ.get("ADMINUSER_PASS", User.objects.make_random_password())
        admin = User(
            username=options["user"], email=options["email"], is_superuser=True
        )
        admin.set_password(password)
        admin.save()

        self.stdout.write(
            self.style.SUCCESS("Created superuser named {user}".format(**options))
        )
        if password_source == "random":
            self.stdout.write("Password: " + password)
