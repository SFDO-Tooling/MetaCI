from django.utils import timezone
from django.core.management.base import BaseCommand, CommandError
from scheduler.models import RepeatableJob

class Command(BaseCommand):
    help = 'Returns the API token for a given username.  If one does not exist, a token is first created.'

    def handle(self, *args, **options):
        job, created = RepeatableJob.objects.get_or_create(
            callable = 'metaci.build.tasks.check_waiting_builds',
            enabled = True,
            name = 'check_waiting_builds',
            queue = 'short',
            defaults={
                'interval': 1,
                'interval_unit': 'minutes',
                'scheduled_time': timezone.now(),
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS('Created job check_waiting_builds with id {}'.format(job.id)))
        else:
            self.stdout.write(self.style.SUCCESS('Scheduled job check_waiting_builds with id {} already exists and is {}.'.format(job.id, 'enabled' if job.enabled else 'disabled')))
