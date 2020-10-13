from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from metaci.build.models import BuildFlow
from metaci.testresults.models import TestResult


class Command(BaseCommand):
    help = "Deletes old test results and clears build logs (> 1 year old)."

    def handle(self, *args, **options):
        year_ago = timezone.now() - timedelta(days=365)

        # flow logs
        build_flows = BuildFlow.objects.filter(time_queue__lte=year_ago)
        count = build_flows.count()
        self.stdout.write(
            f"Clearing {count} build flow logs from over a year ago...", ending=""
        )
        build_flows.update(log="")
        self.stdout.write("Done.")

        # test results
        old_test_results = TestResult.objects.filter(
            build_flow__time_queue__lte=year_ago
        )
        count = old_test_results.count()
        self.stdout.write(
            f"Deleting {count} test results from over a year ago...", ending=""
        )
        old_test_results.delete()
        self.stdout.write("Done.")
