from datetime import timedelta
from typing import Iterable

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from metaci.build.models import BuildFlow
from metaci.testresults.models import TestResult, TestResultAsset


class Command(BaseCommand):
    help = "Deletes old test results and clears build logs (> 1 year old)."

    def handle(self, *args, **options):
        year_ago = timezone.now() - timedelta(days=365)

        def show_progress(source: Iterable, batch_size: int = 1000):
            i = 0
            for item in source:
                i += 1
                yield item
                if not i % batch_size:
                    self.stdout.write(str(i))

        # flow logs
        build_flows = BuildFlow.objects.filter(time_queue__lte=year_ago)
        count = build_flows.count()
        self.stdout.write(f"Clearing {count} build flow logs from over a year ago...")
        build_flows.update(log="")
        self.stdout.write("Done.\n")

        # test result assets
        old_assets = TestResultAsset.objects.filter(
            result__build_flow__time_queue__lte=year_ago
        )
        count = old_assets.count()
        self.stdout.write(
            f"Deleting {count} test result assets from over a year ago..."
        )
        with transaction.atomic():
            for asset in show_progress(old_assets.iterator()):
                asset.asset.delete()
                asset.delete()
        self.stdout.write("Done.\n")

        # test results
        old_test_results = TestResult.objects.filter(
            build_flow__time_queue__lte=year_ago
        )
        count = old_test_results.count()
        self.stdout.write(f"Deleting {count} test results from over a year ago...")
        # Raw delete avoids the model layer entirely,
        # and avoids loading the existing models into memory to handle things like cascade-delete.
        # It's okay here because we already deleted the TestResultAssets,
        # and aren't using signals with this model.
        old_test_results._raw_delete(old_test_results.db)
        self.stdout.write("Done.\n")
