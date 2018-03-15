from django.contrib.auth.models import AnonymousUser
from django.core.management.base import BaseCommand

from metaci.build.models import Build
from metaci.build.models import Rebuild


class Command(BaseCommand):
    # NOTE: This should only be run at heroku postdeploy stage
    help = 'Rebuild all builds/rebuilds with status "running"'

    def handle(self, *args, **options):
        user = AnonymousUser()
        for rebuild in Rebuild.objects.filter(status='running'):
            rebuild.status = 'error'
            rebuild.save()
            Rebuild.objects.create(
                build=rebuild.build,
                user=user,
                status='queued',
            )
        for build in Build.objects.filter(status='running'):
            build.status = 'error'
            build.save()
            Rebuild.objects.create(
                build=build,
                user=user,
                status='queued',
            )
