from rq import requeue_job
from rq.exceptions import ShutDownImminentException


class BuildError(Exception):
    pass


def requeue_on_imminent_shutdown(job, exc_type, exc_value, traceback):
    # If the worker aborted due to a Heroku dyno restart, requeue the job.
    if isinstance(exc_value, ShutDownImminentException):
        requeue_job(job.id)
        return False
