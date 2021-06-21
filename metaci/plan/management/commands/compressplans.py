from itertools import combinations

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from metaci.plan.models import Plan, PlanRepository
from metaci.utils import is_attr_equal


class Command(BaseCommand):
    help = '"Compress" plans by merging redundant plans into a single plan'

    def add_arguments(self, parser):
        parser.add_argument(
            "--delete",
            action="store_true",
            dest="delete",
            default=False,
            help="Delete plan instead of deactivating",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            dest="dry_run",
            default=False,
            help="Do a dry run (do not modify db)",
        )

    def handle(self, *args, **options):
        if options["dry_run"]:
            self.stdout.write("DRY RUN - db will not be modified")
        invalid_plans = set()
        plan_pks = sorted([plan.pk for plan in Plan.objects.all()])
        for plan_combo in combinations(plan_pks, 2):
            # skip combo if either plan is deleted or deactivated
            if set(plan_combo).intersection(invalid_plans):
                continue
            plan1 = Plan.objects.get(pk=plan_combo[0])
            plan2 = Plan.objects.get(pk=plan_combo[1])
            # skip if plans are not equal for these fields
            if not is_attr_equal(
                plan1,
                plan2,
                [
                    "role",
                    "trigger",
                    "regex",
                    "flows",
                    "org",
                    "context",
                    "active",
                    "dashboard",
                    "junit_path",
                    "sfdx_config",
                    "yaml_config",
                ],
            ):
                continue
            # keep the plan with more builds
            if plan1.builds.count() < plan2.builds.count():
                # swap plans (keep plan1)
                plan1, plan2 = plan2, plan1
            # reassign builds to the plan we're keeping (plan1)
            with transaction.atomic():
                for build in plan2.builds.select_for_update():
                    self.stdout.write(
                        self.style.WARNING(
                            f"Overwriting Plan ({build.plan} --> {plan1}) for Build {build}"
                        )
                    )
                    build.plan = plan1
                    if not options["dry_run"]:
                        build.save()
            # copy all repos to the plan we're keeping
            for repo in plan2.repos.all():
                try:
                    PlanRepository.objects.get(plan=plan1, repo=repo)
                except PlanRepository.DoesNotExist:
                    self.stdout.write(
                        self.style.WARNING(f"Linking Repository {repo} to Plan {plan1}")
                    )
                    if not options["dry_run"]:
                        PlanRepository.objects.create(plan=plan1, repo=repo)
            # delete/deactivate plan
            invalid_plans.add(plan2.pk)
            if options["delete"]:
                self.stdout.write(self.style.WARNING(f"Deleting Plan {plan2}"))
                if not options["dry_run"]:
                    plan2.delete()
            else:
                self.stdout.write(self.style.WARNING(f"Deactivating Plan {plan2}"))
                plan2.active = False
                if not options["dry_run"]:
                    plan2.save()
