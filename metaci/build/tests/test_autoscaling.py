import os
import json
import pytest
import responses
from unittest import mock

from metaci.build.autoscaling import (
    Autoscaler,
    HerokuAutoscaler,
    LocalAutoscaler,
    autoscale,
    get_autoscaler,
)


@pytest.fixture
def non_scaler_config():
    return {"queues": ["default", "medium", "high"]}


@pytest.fixture
def scaler_config():
    return {
        "app_name": "test-app",
        "worker_type": "worker",
        "queues": ["default", "medium", "high"],
    }


class TestAutoscaler:
    @mock.patch("django_rq.get_queue")
    @mock.patch("metaci.build.autoscaling.Autoscaler.count_builds")
    def test_measure(self, count_builds, get_queue):
        high_priority_queue = mock.Mock()
        high_priority_queue.name = "high"
        get_queue.side_effect = [high_priority_queue, mock.Mock(), mock.Mock()]
        count_builds.side_effect = [1, 0, 2]

        autoscaler = Autoscaler(config={"queues": ["default", "medium", "high"]})
        autoscaler.measure()
        assert autoscaler.active_builds == 3
        assert autoscaler.target_workers == 3

    def test_repr(self, non_scaler_config):
        autoscaler = Autoscaler(non_scaler_config)
        assert repr(autoscaler) == "<Autoscaler builds: 0, workers: 0>"

    @mock.patch("metaci.build.autoscaling.StartedJobRegistry")
    def test_count_builds(self, StartedJobRegistry, non_scaler_config):
        queue = mock.Mock(count=1)
        StartedJobRegistry.return_value = [mock.Mock]
        autoscaler = Autoscaler(non_scaler_config)
        assert autoscaler.count_builds(queue) == 2

    @mock.patch("metaci.build.autoscaling.Worker")
    def test_count_workers(self, Worker, non_scaler_config):
        Worker.count.return_value = 1
        autoscaler = Autoscaler(non_scaler_config)
        assert autoscaler.count_workers() == 1

    @mock.patch("metaci.build.autoscaling.get_autoscaler")
    def test_autoscale(self, get_autoscaler):
        get_autoscaler.return_value.target_workers = 1
        scale_info = autoscale()
        assert scale_info["test-app"] == 1


class TestLocalAutoscaler:
    @mock.patch("subprocess.Popen")
    def test_scale__up(self, Popen, non_scaler_config):
        autoscaler = LocalAutoscaler(non_scaler_config)
        autoscaler.active_builds = 1
        autoscaler.target_workers = 1
        autoscaler.count_workers = mock.Mock(return_value=0)
        autoscaler.scale()
        Popen.assert_called_once()

    def test_scale__down(self, non_scaler_config):
        autoscaler = LocalAutoscaler(non_scaler_config)
        autoscaler.active_builds = 0
        LocalAutoscaler.processes = [mock.Mock()]
        autoscaler.scale()
        assert LocalAutoscaler.processes == []


class TestHerokuAutoscaler:
    @responses.activate
    def test_scale__up(self, scaler_config):
        responses.add(
            "PATCH",
            "https://api.heroku.com/apps/test-app/formation/worker",
            status=200,
            json={},
        )

        autoscaler = HerokuAutoscaler(scaler_config)
        autoscaler.target_workers = 1
        autoscaler.count_workers = mock.Mock(return_value=0)
        autoscaler.scale()

    @responses.activate
    def test_scale__down(self, scaler_config):
        responses.add(
            "PATCH",
            "https://api.heroku.com/apps/test-app/formation/worker",
            status=200,
            json={},
        )

        autoscaler = HerokuAutoscaler(scaler_config)
        autoscaler.active_builds = 0
        autoscaler.count_workers = mock.Mock(return_value=1)
        autoscaler.scale()

    @responses.activate
    def test_scale__overask(self, scaler_config):
        def request_callback(request):
            data = json.loads(request.body)
            if data["quantity"] > 98:
                return (
                    422,
                    {},
                    json.dumps({"limit": 100, "id": "cannot_update_above_limit"}),
                )
            else:
                return (200, {}, '{"id":"passport"}')

        responses.add_callback(
            "PATCH",
            "https://api.heroku.com/apps/test-app/formation/worker",
            callback=request_callback,
        )
        responses.add(
            "GET",
            "https://api.heroku.com/apps/test-app/formation",
            status=200,
            json=[
                {"quantity": 5, "type": "worker"},
                {"quantity": 1, "type": "worker_short"},
                {"quantity": 0, "type": "dev_worker"},
                {"quantity": 0, "type": "release"},
                {"quantity": 1, "type": "web"},
            ],
        )

        autoscaler = HerokuAutoscaler(scaler_config)
        autoscaler.active_builds = 3
        autoscaler.target_workers = 100
        autoscaler.count_workers = mock.Mock(return_value=1)
        autoscaler.scale()


def test_get_autoscaler():
    """In test context autoscaler is set to metaci.build.autoscaling.LocalAutoscaler"""
    autoscaler_class = get_autoscaler("test-app")
    assert isinstance(autoscaler_class, LocalAutoscaler)
