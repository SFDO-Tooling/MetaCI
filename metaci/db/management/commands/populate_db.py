from django.core.management.base import BaseCommand

from django.db import transaction

from guardian.shortcuts import assign_perm

import factory.random

from metaci import conftest as fact
from metaci.users.models import User
from metaci.testresults.models import TestResult
from django.contrib.auth.models import Group

from metaci.build.models import BuildFlow, Build


class Command(BaseCommand):
    help = "Populates a testing DB with sample data"

    def handle(self, *args, **options):
        if self.check_non_destructive():
            print("Populating test data")
            # reset_db.Command().handle(*args, **options)
            # migrate.Command().handle(*args, **options)

            self.create_objs()
        else:
            print(
                """
            This does not seem to be an empty or test database!
            Please clear the database before continuing!
            One way of clearing the database is:

            python manage.py reset_db -c && python manage.py migrate && python manage.py createsuperuser --username clark --email kent@krypton.com

            You can add a --noinput to that if you're sure you know what you're doing.
            """
            )

    def check_non_destructive(self):
        return User.objects.count() < 3 and TestResult.objects.count() < 10

    def create_objs(self):
        with transaction.atomic():
            factory.random.reseed_random("TOtaLLY RaNdOM")
            fact.UserFactory()
            fact.UserFactory()
            PublicPlanRepository = fact.PlanRepositoryFactory()
            PrivatePlanRepository = fact.PlanRepositoryFactory()
            assign_perm(
                "plan.view_builds",
                Group.objects.get(name="Public"),
                PublicPlanRepository,
            )

            fact.TestResultFactory(build_flow__build__planrepo=PublicPlanRepository)
            fact.TestResultFactory(build_flow__build__planrepo=PrivatePlanRepository)
            fact.TestResultFactory(build_flow__build__planrepo=PublicPlanRepository)
            fact.TestResultFactory(build_flow__build__planrepo=PrivatePlanRepository)

            self.make_consistent()

    def make_consistent(self):
        for bf in BuildFlow.objects.all():
            bf.tests_total = bf.test_results.count()
            bf.save()
