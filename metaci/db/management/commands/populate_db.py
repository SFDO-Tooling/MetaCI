from django.core.management.base import BaseCommand

from metaci import conftest as fact
from metaci.users.models import User
from metaci.testresults.models import TestResult


class Command(BaseCommand):
    help = "Populates a testing DB with sample data"

    def handle(self, *args, **options):
        if self.check_non_destructive():
            print("Okay", args)
            # reset_db.Command().handle(*args, **options)
            # migrate.Command().handle(*args, **options)

            self.create_objs()
        else:
            print(
                """
            This does not seem to be an empty or test database!
            Please clear the database before continuing!
            One way of clearing the database is:

            python manage.py reset_db -c && python manage.py migrate

            You can add a --noinput to that if you're sure you know what you're doing.
            """
            )

    def check_non_destructive(self):
        return User.objects.count() < 2 and TestResult.objects.count() < 50

    def create_objs(self):
        user1 = fact.UserFactory()
        user2 = fact.UserFactory()
        superuser = fact.StaffSuperuserFactory()
        TestMethod1 = fact.TestMethodFactory()
        TestMethod2 = fact.TestMethodFactory()
        (user1, user2, superuser, TestMethod1, TestMethod2)  # quiet linter
