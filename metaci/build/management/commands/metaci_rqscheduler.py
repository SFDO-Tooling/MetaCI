import logging

import django_rq
from django.conf import settings
from django_rq.management.commands import rqscheduler

logger = logging.getLogger(__name__)


def register_scheduled_jobs():
    scheduler = django_rq.get_scheduler("short")

    # Cancel existing jobs
    for job in scheduler.get_jobs():
        scheduler.cancel(job)

    # Schedule jobs from settings
    for job_id, kwargs in settings.CRON_JOBS.items():
        for key in ("cron_string", "func"):
            if key not in kwargs:
                raise TypeError(f"CRON_JOBS['{job_id}'] is missing {key}")
        kwargs["queue_name"] = kwargs.get("queue_name") or "short"
        kwargs["use_local_timezone"] = True
        scheduler.cron(**kwargs)
        logger.info(f"Scheduled job {job_id}: {kwargs})")


class Command(rqscheduler.Command):
    """Update scheduled jobs in redis, then run rqscheduler

    Extends django-rq's rqscheduler command.
    """

    def handle(self, *args, **kw):
        register_scheduled_jobs()
        super(Command, self).handle(*args, **kw)
