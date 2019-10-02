import logging
import subprocess

import django_rq
import requests
from cumulusci.core.utils import import_global
from django.conf import settings
from rq import Worker
from rq.registry import StartedJobRegistry

logger = logging.getLogger(__name__)
QUEUES = ("high", "medium", "default")


class Autoscaler(object):
    def __init__(self):
        self.queues = [django_rq.get_queue(name) for name in QUEUES]
        self.active_builds = sum(
            queue.count + len(StartedJobRegistry(queue=queue)) for queue in self.queues
        )
        # use as many workers as we have builds or our max (whichever is less)
        # but also keep aside a reserve for high-priority builds
        max_workers = settings.METACI_MAX_WORKERS - settings.METACI_WORKER_RESERVE
        self.target_workers = min(self.active_builds, max_workers)
        # if there's a backlog of high-priority builds, use the reserve
        high_priority_backlog = django_rq.get_queue("high").count
        if self.active_builds > max_workers and high_priority_backlog:
            self.target_workers += min(
                high_priority_backlog, settings.METACI_WORKER_RESERVE
            )

    def __repr__(self):
        return f"<{self.__class__} builds: {self.active_builds}, workers: {self.target_workers}>"

    def count_workers(self):
        return Worker.count(queue=self.queues[0])

    def scale(self):
        pass


class NonAutoscaler(Autoscaler):
    """Don't actually autoscale."""


class LocalAutoscaler(Autoscaler):
    """Scale by starting rqworker subprocesses in burst mode."""

    processes = []

    def scale(self):
        if not self.active_builds:
            LocalAutoscaler.processes = []
        else:
            count = self.target_workers - self.count_workers()
            if count > 0:
                logger.info(f"Starting {count} workers in burst mode")
                for x in range(count):
                    self.processes.append(
                        subprocess.Popen(
                            [
                                "python",
                                "./manage.py",
                                "rqworker",
                                "high",
                                "medium",
                                "default" "--burst",
                            ]
                        )
                    )


class HerokuAutoscaler(Autoscaler):
    """Scale using Heroku worker dynos."""

    def scale(self):
        url = f"https://api.heroku.com/apps/{settings.HEROKU_APP_NAME}/formation/worker"
        headers = {
            "Accept": "application/vnd.heroku+json; version=3",
            "Authorization": f"Bearer {settings.HEROKU_TOKEN}",
        }
        # We should only scale down if there are no active builds,
        # because we don't know which worker will be stopped.
        active_workers = self.count_workers()
        if active_workers and not self.active_builds:
            logger.info(f"Scaling down to 0 workers")
            resp = requests.patch(url, json={"quantity": 0}, headers=headers)
            resp.raise_for_status()
        elif self.target_workers > active_workers:
            logger.info(f"Scaling up to {self.target_workers} workers")
            resp = requests.patch(
                url, json={"quantity": self.target_workers}, headers=headers
            )
            resp.raise_for_status()


get_autoscaler = import_global(settings.METACI_WORKER_AUTOSCALER)


@django_rq.job("short")
def autoscale():
    autoscaler = get_autoscaler()
    autoscaler.scale()
    return autoscaler.target_workers


# to do:
# - test on heroku
# - test coverage
# - fix requeueing
