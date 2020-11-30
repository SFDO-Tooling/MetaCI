from django.core.management.base import BaseCommand
from django.utils import timezone
from scheduler.models import RepeatableJob


class Command(BaseCommand):
    help = "Creates a RepeatableJob to check for waiting builds."

    def handle(self, *args, **options):
        job, created = RepeatableJob.objects.get_or_create(
            callable="metaci.build.tasks.check_waiting_builds",
            enabled=True,
            name="check_waiting_builds",
            queue="short",
            defaults={
                "interval": 1,
                "interval_unit": "minutes",
                "scheduled_time": timezone.now(),
            },
        )
        if created:
            self.stdout.write(
                self.style.SUCCESS(
                    f"Created job check_waiting_builds with id {job.id}"
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f"Scheduled job check_waiting_builds with id {job.id} "
                    + f"already exists and is {'enabled' if job.enabled else 'disabled'}."
                )
            )
