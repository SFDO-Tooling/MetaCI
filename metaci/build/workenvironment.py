import os
import signal
import subprocess
from abc import ABC, abstractmethod

import requests
from django.conf import settings


class WorkEnvironment(ABC):
    @abstractmethod
    def scale_to(self, quantity):
        pass

    @abstractmethod
    def stop_worker(self, worker_id):
        pass

    @abstractmethod
    def get_worker_id_from_environment(self):
        pass


class LocalWorkEnvironment(WorkEnvironment):
    def scale_to(self, quantity):
        processes = [
            subprocess.Popen(
                [
                    "python",
                    "./manage.py",
                    "rqworker",
                    "high",
                    "medium",
                    "default",
                    "--burst",
                ]
            )
            for x in range(quantity)
        ]
        return processes

    def stop_worker(self, worker_id):
        os.kill(worker_id, signal.SIGTERM)

    def get_worker_id_from_environment(self):
        return os.getpid()


class HerokuWorkEnvironment(WorkEnvironment):
    def __init__(self):
        self.headers = {
            "Accept": "application/vnd.heroku+json; version=3",
            "Authorization": f"Bearer {settings.HEROKU_TOKEN}",
        }

    def scale_to(self, quantity):
        url = f"https://api.heroku.com/apps/{settings.HEROKU_APP_NAME}/formation/worker"
        resp = requests.patch(url, json={"quantity": quantity}, headers=self.headers)
        resp.raise_for_status()

    def stop_worker(self, worker_id):
        url = (
            f"https://api.heroku.com/apps/{settings.HEROKU_APP_NAME}/dynos/{worker_id}"
        )
        resp = requests.delete(url, headers=self.headers)
        resp.raise_for_status()

    def get_worker_id_from_environment(self):
        dyno_id = os.environ.get("DYNO")
        assert dyno_id
        return dyno_id


def get_environment():
    if os.environ.get("DYNO"):
        return HerokuWorkEnvironment()
    else:
        return LocalWorkEnvironment()
