import logging
import subprocess
import typing as T

import django_rq
import requests
from cumulusci.core.utils import import_global
from django.conf import settings
from rq import Worker
from rq.registry import StartedJobRegistry

from metaci.exceptions import ConfigError

logger = logging.getLogger(__name__)


class Autoscaler(object):
    """Utility to adjust the # of workers based on queue size."""

    active_builds = 0
    target_workers = 0

    def __init__(self, config):
        """config is a dict that has an entry for queues"""
        if "queues" not in config:
            raise ConfigError(
                f"'queues' not present in autoscaler config:\nFound: {config}"
            )
        self.queues = [django_rq.get_queue(name) for name in config["queues"]]

        if "max_workers" not in config:
            raise ConfigError(
                f"'max_workers' not present in autoscaler config:\nFound: {config}"
            )
        self.max_workers = config["max_workers"]

        if "worker_reserve" not in config:
            raise ConfigError(
                f"'worker_reserve' not present in autoscaler config:\nFound: {config}"
            )
        self.worker_reserve = config["worker_reserve"]

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
        reserve_workers = min(high_priority_builds, self.worker_reserve)
        other_workers = min(
            self.active_builds - reserve_workers,
            self.max_workers - self.worker_reserve,
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


class OneOffBuilder(object):
    def __init__(self, config):
        pass

    def one_off_build(self, build_id: T.Union[int, str], lock_id: str):
        """Run a build outside of the scaling formation"""


class NonAutoscaler(Autoscaler):
    """Don't actually autoscale."""


class LocalAutoscaler(Autoscaler):
    """Scale by starting rqworker subprocesses in burst mode."""

    processes = []

    def scale(self):
        if not self.active_builds:
            # Workers in burst mode will stop themselves once the queue is empty;
            # we just need to clear our references.
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
                                "metaci_rqworker",
                                "high",
                                "medium",
                                "default",
                                "--burst",
                            ]
                        )
                    )


class LocalOneOffBuilder(OneOffBuilder):
    def one_off_build(self, build_id: T.Union[int, str], lock_id: str):
        """Run a build in a sub-process"""
        lock_id = lock_id or "none"
        proc = subprocess.Popen(
            ["python", "./manage.py", "run_build_from_id", str(build_id), lock_id]
        )
        return proc.pid


class HerokuAutoscaler(Autoscaler):
    """Scale using Heroku worker dynos."""

    API_ROOT = "https://api.heroku.com/apps"

    def __init__(self, config):
        """config is a dict which has entries for: app_name, worker_type, and queues."""

        if "app_name" not in config:
            raise ConfigError(
                f"'app_name' not present in autoscaler config:\nFound: {config}"
            )
        self.app_name = config["app_name"]

        if "worker_type" not in config:
            raise ConfigError(
                f"'worker_type' not present in autoscaler config:\nFound: {config}"
            )
        self.worker_type = config["worker_type"]
        self.base_url = f"{self.API_ROOT}/{config['app_name']}"
        self.url = f"{self.base_url}/formation/{self.worker_type}"
        self.headers = {
            "Accept": "application/vnd.heroku+json; version=3",
            "Authorization": f"Bearer {settings.HEROKU_TOKEN}",
        }
        super().__init__(config)

    def scale(self):
        # We should only scale down if there are no active builds,
        # because we don't know which worker will be stopped.
        active_workers = self.count_workers()
        if active_workers and not self.active_builds:
            self._scale_down(num_workers=0)
        elif self.target_workers > active_workers:
            self._scale_up(num_workers=self.target_workers)

    def _scale_down(self, num_workers):
        logger.info(
            f"Scaling app ({self.app_name}) down to {num_workers} workers of type: {self.worker_type}"
        )
        resp = requests.patch(
            self.url, json={"quantity": num_workers}, headers=self.headers
        )
        resp.raise_for_status()

    def _scale_up(self, num_workers):
        logger.info(
            f"Scaling app ({self.app_name}) up to {self.target_workers} workers"
        )
        resp = requests.patch(
            self.url, json={"quantity": self.target_workers}, headers=self.headers
        )
        if resp.json() and resp.json().get("id") == "cannot_update_above_limit":
            limit = resp.json()["limit"]
            resp = self.scale_max(self.url, self.headers, self.worker_type, limit)

        resp.raise_for_status()

    def scale_max(self, url, headers, worker_type, limit):
        base_url, _ = url.rsplit("/", 1)
        dyno_types = requests.get(base_url, headers=headers).json()
        used_by_others = sum(
            x["quantity"] for x in dyno_types if x["type"] != worker_type
        )
        target_workers = limit - used_by_others
        assert target_workers >= 0

        return requests.patch(url, json={"quantity": target_workers}, headers=headers)


class HerokuOneOffBuilder(OneOffBuilder):
    """Run a build in a Heroku one-off dyno."""

    API_ROOT = "https://api.heroku.com/apps"

    def __init__(self, config):
        assert (
            "app_name" in config
        ), "METACI_LONG_RUNNING_BUILD_CONFIG should include app_name"
        self.base_url = f"{self.API_ROOT}/{config['app_name']}"
        self.headers = {
            "Accept": "application/vnd.heroku+json; version=3",
            "Authorization": f"Bearer {settings.HEROKU_TOKEN}",
        }
        super().__init__(config)

    def one_off_build(self, build_id: T.Union[int, str], lock_id: str):
        """Run a one-off-build on a new heroku dyno"""
        lock_id = lock_id or "none"
        command = " ".join(
            ["python", "./manage.py", "run_build_from_id", str(build_id), lock_id]
        )
        url = f"{self.base_url}/dynos"
        json = {"command": command, "time_to_live": "86400"}

        resp = requests.post(url, json=json, headers=self.headers)
        if resp.status_code != 200:
            msg = f"One-off dyno could not be started: {resp.status_code}: {resp.reason} : {resp.text}"
            logger.error(msg)
            resp.raise_for_status()
        return resp.json()["id"]


def get_autoscaler(app_name):
    """Fetches the appropriate autoscaler given the app name"""
    autoscaler_class = import_global(settings.METACI_WORKER_AUTOSCALER)
    return autoscaler_class(settings.AUTOSCALERS[app_name])


@django_rq.job("short")
def autoscale():
    """Apply autoscaling.

    This is meant to run frequently via rqscheduler.
    """
    scaling_info = {}
    for app_name in settings.AUTOSCALERS.keys():
        autoscaler = get_autoscaler(app_name)
        autoscaler.measure()
        autoscaler.scale()
        scaling_info[app_name] = autoscaler.target_workers

    return scaling_info
