import json
from unittest import mock

import pytest
import responses

from metaci.build.autoscaling import HerokuOneOffBuilder, LocalOneOffBuilder


@pytest.mark.django_db
class TestLocalOneOffBuilder:
    @mock.patch("subprocess.Popen")
    def test_local_one_off_build(self, Popen, data):
        builder = LocalOneOffBuilder({})

        builder.one_off_build(data["build"].id, "abcdef")
        Popen.assert_called_once_with(
            ["python", "./manage.py", "run_build_from_id", mock.ANY, "abcdef"]
        )


@pytest.mark.django_db
class TestHerokuOneOffBuilder:
    @responses.activate
    def test_heroku_one_off_build(self, data):
        builder = HerokuOneOffBuilder({"app_name": "test-app"})

        def matcher(post):
            postdata = json.loads(post)

            assert postdata == {
                "command": f"python ./manage.py run_build_from_id {data['build'].id} abcdef",
                "time_to_live": "86400",
            }
            return True

        responses.add(
            "POST",
            "https://api.heroku.com/apps/test-app/dynos",
            status=200,
            match=[matcher],
            json={"id": "23"},
        )

        builder.one_off_build(data["build"].id, "abcdef")
