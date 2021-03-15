from django.core.management.base import BaseCommand

from metaci.build.management.commands._utils import do_build


class Command(BaseCommand):
    help = "Runs a build from the command line (on local computer)."

    def add_arguments(self, parser):
        parser.add_argument("build_id", type=str)

    def handle(self, build_id, *args, **options):
        do_build(build_id, options)
