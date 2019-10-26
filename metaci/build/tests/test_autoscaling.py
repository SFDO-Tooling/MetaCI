import json
from unittest import mock

import responses

from metaci.build.autoscaling import (
    Autoscaler,
    HerokuAutoscaler,
    LocalAutoscaler,
    autoscale,
)


class TestAutoscaler:
    @mock.patch("django_rq.get_queue")
    @mock.patch("metaci.build.autoscaling.Autoscaler.count_builds")
    def test_measure(self, count_builds, get_queue):
        high_priority_queue = mock.Mock()
        high_priority_queue.name = "high"
        get_queue.side_effect = [high_priority_queue, mock.Mock(), mock.Mock()]
        count_builds.side_effect = [1, 0, 2]

        autoscaler = Autoscaler()
        autoscaler.measure()
        assert autoscaler.active_builds == 3
        assert autoscaler.target_workers == 3

    def test_repr(self):
        autoscaler = Autoscaler()
        assert repr(autoscaler) == "<Autoscaler builds: 0, workers: 0>"

    @mock.patch("metaci.build.autoscaling.StartedJobRegistry")
    def test_count_builds(self, StartedJobRegistry):
        queue = mock.Mock(count=1)
        StartedJobRegistry.return_value = [mock.Mock]
        autoscaler = Autoscaler()
        assert autoscaler.count_builds(queue) == 2

    @mock.patch("metaci.build.autoscaling.Worker")
    def test_count_workers(self, Worker):
        Worker.count.return_value = 1
        autoscaler = Autoscaler()
        assert autoscaler.count_workers() == 1

    @mock.patch("metaci.build.autoscaling.get_autoscaler")
    def test_autoscale(self, get_autoscaler):
        get_autoscaler.return_value.target_workers = 1
        target_workers = autoscale()
        assert target_workers == 1


class TestLocalAutoscaler:
    @mock.patch("subprocess.Popen")
    def test_scale__up(self, Popen):
        autoscaler = LocalAutoscaler()
        autoscaler.active_builds = 1
        autoscaler.target_workers = 1
        autoscaler.count_workers = mock.Mock(return_value=0)
        autoscaler.scale()
        Popen.assert_called_once()

    def test_scale__down(self):
        autoscaler = LocalAutoscaler()
        autoscaler.active_builds = 0
        LocalAutoscaler.processes = [mock.Mock()]
        autoscaler.scale()
        assert LocalAutoscaler.processes == []


class TestHerokuAutoscaler:
    @responses.activate
    def test_scale__up(self):
        responses.add(
            "PATCH",
            "https://api.heroku.com/apps/testapp/formation/worker",
            status=200,
            json={},
        )

        autoscaler = HerokuAutoscaler()
        autoscaler.target_workers = 1
        autoscaler.count_workers = mock.Mock(return_value=0)
        autoscaler.scale()

    @responses.activate
    def test_scale__down(self):
        responses.add(
            "PATCH",
            "https://api.heroku.com/apps/testapp/formation/worker",
            status=200,
            json={},
        )

        autoscaler = HerokuAutoscaler()
        autoscaler.active_builds = 0
        autoscaler.count_workers = mock.Mock(return_value=1)
        autoscaler.scale()

    @responses.activate
    def test_scale__overask(self):
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
            "https://api.heroku.com/apps/testapp/formation/worker",
            callback=request_callback,
        )
        responses.add(
            "GET",
            "https://api.heroku.com/apps/testapp/formation",
            status=200,
            json=[
                {"quantity": 5, "type": "worker"},
                {"quantity": 1, "type": "worker_short"},
                {"quantity": 0, "type": "dev_worker"},
                {"quantity": 0, "type": "release"},
                {"quantity": 1, "type": "web"},
            ],
        )

        autoscaler = HerokuAutoscaler()
        autoscaler.active_builds = 3
        autoscaler.target_workers = 100
        autoscaler.count_workers = mock.Mock(return_value=1)
        autoscaler.scale()
