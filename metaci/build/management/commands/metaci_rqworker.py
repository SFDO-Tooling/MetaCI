import os

from django.conf import settings
from django_rq.management.commands.rqworker import Command as BaseCommand


class Command(BaseCommand):
    def handle(self, *args, **options):
        # If the DYNO environment variable is set, we are probably on Heroku.
        dyno = os.environ.get("DYNO")
        if dyno:
            # Reserve highest numbered dynos for high-priority builds only
            number = int(dyno.split(".")[-1])
            if number > settings.METACI_MAX_WORKERS - settings.METACI_WORKER_RESERVE:
                args = ["high"]

            # Use the HerokuWorker.
            # This ensures that workers exit in a way that can requeue running jobs.
            options["worker_class"] = "rq.worker.HerokuWorker"

        if "sentry_dsn" not in options:
            options["sentry_dsn"] = ""

        return super().handle(*args, **options)
