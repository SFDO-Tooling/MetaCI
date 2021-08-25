import os

from django.conf import settings
from django_rq.management.commands.rqworker import Command as BaseCommand
from rq.exceptions import ShutDownImminentException
from rq.worker import HerokuWorker


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

        return super().handle(*args, **options)


# Raise ShutDownImminentException immediately; no reason to dilly-dally
HerokuWorker.imminent_shutdown_delay = 0

# As defined in rq, ShutDownImminentException extends Exception.
# That means it will get caught by all `except Exception` handlers,
# which is frustrating because we want it to fall through everything
# to the requeue_on_imminent_shutdown exception handler.
# Extending BaseException instead will let it do that.
ShutDownImminentException.__bases__ = (BaseException,)
