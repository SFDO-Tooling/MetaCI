import logging

import django_rq
from django.conf import settings
from django_rq.management.commands import rqscheduler

logger = logging.getLogger(__name__)


def register_cron_jobs(jobs: dict, queue_name: str):
    """Replace the existing cron jobs for the specified rq queue.

    Removes all existing scheduled jobs, then adds new ones.

    `jobs` should be a dict:
    - keys are strings identifying the jobs
    - values are a dict to pass to scheduler.cron(), with at least:
        - `func` (dotted path to callable)
        - `cron_string` (schedule in cron format)
    """
    scheduler = django_rq.get_scheduler(queue_name)

    # Cancel existing jobs
    for job in list(scheduler.get_jobs()):
        scheduler.cancel(job)

    # Schedule jobs from settings
    for job_id, kwargs in jobs.items():
        for key in ("cron_string", "func"):
            if key not in kwargs:
                raise TypeError(f"Scheduled job {job_id} is missing {key}")
        kwargs["queue_name"] = queue_name
        kwargs["use_local_timezone"] = True
        scheduler.cron(**kwargs)
        logger.info(f"Scheduled job {job_id}: {kwargs})")


class Command(rqscheduler.Command):
    """Update scheduled rq jobs, then run rqscheduler

    Extends django-rq's rqscheduler command.
    """

    def handle(self, *args, **kw):
        queue_name = kw.get("queue") or "short"
        register_cron_jobs(settings.CRON_JOBS, queue_name)
        super(Command, self).handle(*args, **kw)
