from django.core.management.base import BaseCommand

from metaci.build.models import Build

from .run_build import run_build_from_django_command


class Command(BaseCommand):
    help = "Runs a build from the command line (on local computer)."

    def add_arguments(self, parser):
        parser.add_argument("build_id", type=str)
        parser.add_argument("lock_id", type=str)

    def handle(self, build_id, lock_id, *args, **options):
        build = Build.objects.get(id=build_id)
        if lock_id.lower() == "none":
            lock_id = None

        run_build_from_django_command(build, lock_id)
