import logging
import subprocess

import django_rq
import requests
from cumulusci.core.utils import import_global
from django.conf import settings
from rq import Worker
from rq.registry import StartedJobRegistry

STARTING_WORKERS_KEY = "metaci:starting"
logger = logging.getLogger(__name__)


class Autoscaler(object):
    def __init__(self, queue="default"):
        self.queue = django_rq.get_queue("default")
        self.target_workers = self.active_workers = self.count_workers()
        self.active_builds = len(StartedJobRegistry(queue=self.queue))

    def __repr__(self):
        return (
            f"<Autoscaler workers: {self.active_workers}, builds: {self.active_builds}>"
        )

    def count_workers(self):
        return Worker.count(queue=self.queue)

    def allocate_worker(self, high_priority=False):
        reserve_capacity = 0 if high_priority else settings.METACI_WORKER_RESERVE
        if (
            self.active_builds >= self.target_workers
            and self.target_workers < settings.METACI_MAX_WORKERS - reserve_capacity
        ):
            self.target_workers += 1

    def build_started(self):
        self.active_builds += 1

    def apply_formation(self):
        pass


class NonAutoscaler(Autoscaler):
    """Don't actually autoscale."""

    def allocate_worker(self, high_priority=False):
        pass


class LocalAutoscaler(Autoscaler):
    """Scale by starting rqworker subprocesses in burst mode."""

    processes = []

    def apply_formation(self):
        if not self.active_builds:
            LocalAutoscaler.processes = []
        else:
            count = self.target_workers - self.count_workers()
            if count > 0:
                logger.info(f"Starting {count} workers in burst mode")
                for x in range(count):
                    self.processes.append(
                        subprocess.Popen(
                            ["python", "./manage.py", "rqworker", "default", "--burst"]
                        )
                    )


class HerokuAutoscaler(Autoscaler):
    """Scale using Heroku worker dynos."""

    def apply_formation(self):
        url = f"https://api.heroku.com/apps/{settings.HEROKU_APP_NAME}/formation/worker"
        headers = {
            "Accept": "application/vnd.heroku+json; version=3",
            "Authorization": f"Bearer {settings.HEROKU_TOKEN}",
        }
        # We should only scale down if there are no active builds,
        # because we don't know which worker will be stopped.
        if self.active_workers and not self.active_builds:
            logger.info(f"Scaling down to 0 workers")
            requests.patch(url, json={"quantity": 0}, headers=headers)
        elif self.active_workers > self.count_workers():
            logger.info(f"Scaling up to {self.active_workers} workers")
            requests.patch(url, json={"quantity": self.active_workers}, headers=headers)


if settings.METACI_WORKER_AUTOSCALER:
    get_autoscaler = import_global(settings.METACI_WORKER_AUTOSCALER)
else:
    get_autoscaler = NonAutoscaler


# to do:
# - test heroku scaler on staging
# - test coverage
# - fix requeueing
