import os

from django.conf import settings
from django_rq.management.commands.rqworker import Command as BaseCommand


class Command(BaseCommand):
    def handle(self, *args, **options):
        # Reserve highest numbered dynos for high-priority builds only
        dyno = os.environ.get("DYNO")
        if dyno:
            number = int(dyno.split(".")[-1])
            if number > settings.METACI_MAX_WORKERS - settings.METACI_WORKER_RESERVE:
                args = ["high"]

        return super().handle(*args, **options)
