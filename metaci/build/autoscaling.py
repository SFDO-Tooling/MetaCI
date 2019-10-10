import logging

import django_rq
from cumulusci.core.utils import import_global
from django.conf import settings
from rq import Worker
from rq.registry import StartedJobRegistry

from metaci.build.workenvironment import HerokuWorkEnvironment, LocalWorkEnvironment

logger = logging.getLogger(__name__)


class Autoscaler(object):
    """Utility to adjust the # of workers based on queue size."""

    active_builds = 0
    target_workers = 0

    def __init__(self, queues=("high", "medium", "default")):
        self.queues = [django_rq.get_queue(name) for name in queues]

    def measure(self):
        # Check how many builds are active (queued or started)
        self.active_builds = 0
        high_priority_builds = 0
        for queue in self.queues:
            active_builds = self.count_builds(queue)
            self.active_builds += active_builds
            if queue.name == "high":
                high_priority_builds += active_builds

        # Allocate as many high-priority builds as possible to reserve workers,
        # then the remainder to standard workers
        reserve_workers = min(high_priority_builds, settings.METACI_WORKER_RESERVE)
        other_workers = min(
            self.active_builds - reserve_workers,
            settings.METACI_MAX_WORKERS - settings.METACI_WORKER_RESERVE,
        )
        self.target_workers = reserve_workers + other_workers

    def __repr__(self):
        return f"<{self.__class__.__name__} builds: {self.active_builds}, workers: {self.target_workers}>"

    def count_builds(self, queue):
        return queue.count + len(StartedJobRegistry(queue=queue))

    def count_workers(self):
        """Count how many workers are active

        (Note: this assumes that all workers process the first (high-priority) queue.)
        """
        return Worker.count(queue=self.queues[0])

    def scale(self):
        """Do what is needed to achieve the target # of workers.

        The default is to do no autoscaling.
        """


class NonAutoscaler(Autoscaler):
    """Don't actually autoscale."""


class LocalAutoscaler(Autoscaler):
    """Scale by starting rqworker subprocesses in burst mode."""

    processes = []

    def scale(self):
        work_environment = LocalWorkEnvironment()
        if not self.active_builds:
            # Workers in burst mode will stop themselves once the queue is empty;
            # we just need to clear our references.
            LocalAutoscaler.processes = []
        else:
            count = self.target_workers - self.count_workers()
            if count > 0:
                logger.info(f"Starting {count} workers in burst mode")
                self.processes.append(work_environment.scale_to(count))


class HerokuAutoscaler(Autoscaler):
    """Scale using Heroku worker dynos."""

    def scale(self):
        work_environment = HerokuWorkEnvironment()
        # We should only scale down if there are no active builds,
        # because we don't know which worker will be stopped.
        active_workers = self.count_workers()
        if active_workers and not self.active_builds:
            logger.info(f"Scaling down to 0 workers")
            work_environment.scale_to(0)
        elif self.target_workers > active_workers:
            logger.info(f"Scaling up to {self.target_workers} workers")
            work_environment.scale_to(self.target_workers)


get_autoscaler = import_global(settings.METACI_WORKER_AUTOSCALER)


@django_rq.job("short")
def autoscale():
    """Apply autoscaling.

    This is meant to run frequently as a RepeatableJob.
    """
    autoscaler = get_autoscaler()
    autoscaler.measure()
    autoscaler.scale()
    return autoscaler.target_workers
