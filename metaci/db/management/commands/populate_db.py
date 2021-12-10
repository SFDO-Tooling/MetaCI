import random

import factory.random
from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand
from django.db import transaction
from guardian.shortcuts import assign_perm

from metaci import conftest as fact
from metaci.build.models import BuildFlow
from metaci.cumulusci.models import Org
from metaci.plan.models import Plan, PlanRepository
from metaci.repository.models import Repository
from metaci.testresults.models import TestResult
from metaci.users.models import User


class Command(BaseCommand):
    help = "Populates a testing DB with sample data"

    def add_arguments(self, parser):
        parser.add_argument(
            "--results", action="store_true", help="Create fake builds and test results"
        )

    def handle(self, *args, **options):
        if options["results"]:
            if self.check_non_destructive():
                print("Populating test data")
                # reset_db.Command().handle(*args, **options)
                # migrate.Command().handle(*args, **options)

                self.create_builds_with_test_results()
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
        else:
            self.create_test_repo()

    def check_non_destructive(self):
        return User.objects.count() < 3 and TestResult.objects.count() < 10

    def create_builds_with_test_results(self):
        with transaction.atomic():
            factory.random.reseed_random("TOtaLLY RaNdOM")
            random.seed("RaNDOM!! TOtaLLY")
            fact.UserFactory()
            fact.UserFactory()
            existing_plans = Plan.objects.all()
            PublicPlanRepositories = [
                fact.PlanRepositoryFactory(
                    repo__name_prefix="PublicRepo_", plan=random.choice(existing_plans)
                )
                for i in range(6)
            ]
            PrivatePlanRepositories = [
                fact.PlanRepositoryFactory(
                    repo__name_prefix="PrivateRepo_", plan=random.choice(existing_plans)
                )
                for i in range(6)
            ]
            for repo in PublicPlanRepositories:
                assign_perm("plan.view_builds", Group.objects.get(name="Public"), repo)

            builds = [
                fact.BuildFactory(planrepo=planrepo)
                for planrepo in random.choices(
                    PublicPlanRepositories + PrivatePlanRepositories, k=50
                )
            ]

            build_flows = [
                fact.BuildFlowFactory(build=build)
                for build in random.choices(builds, k=100)
            ]

            methods = [fact.TestMethodFactory() for _ in range(20)]

            test_results = [
                fact.TestResultFactory(build_flow=build_flow, method=method)
                for build_flow, method in zip(
                    random.choices(build_flows, k=200), random.choices(methods, k=200)
                )
            ]
            test_results  # For linter
            self.make_consistent()

    def make_consistent(self):
        for bf in BuildFlow.objects.all():
            bf.tests_total = bf.test_results.count()
            bf.save()

    def create_test_repo(self):
        with transaction.atomic():
            repo = Repository(
                owner="SFDO-Tooling",
                name="CumulusCI-Test",
                github_id=24913646,
                url="https://github.com/SalesforceFoundation/CumulusCI-Test",
            )
            repo.save()
            org = Org(
                name="dev",
                repo=repo,
                json={"config_file":"orgs/dev.json", "scratch":True},
                scratch=True,
            )
            org.save()
            # enable each existing plan for the repo
            for plan in Plan.objects.all():
                planrepo = PlanRepository(plan=plan, repo=repo)
                planrepo.save()
