from unittest import mock

import django_rq
import pytest

from metaci.build.management.commands.metaci_rqscheduler import (
    Command,
    register_cron_jobs,
)


@mock.patch("django_rq.management.commands.rqscheduler.Command.handle")
def test_Command_schedules_jobs(super_handle):
    configured_jobs = {"test": {"func": "test", "cron_string": "* * * * *"}}
    cmd = Command()

    scheduler = django_rq.get_scheduler("short")
    # add an outdated job to make sure it gets cleaned up
    scheduler.cron(func="bogus", cron_string="* * * * *")

    try:
        with mock.patch(
            "metaci.build.management.commands.metaci_rqscheduler.settings.CRON_JOBS",
            configured_jobs,
        ):
            cmd.handle()
    finally:
        actual_jobs = list(scheduler.get_jobs())
        for job in actual_jobs:
            scheduler.cancel(job)

    assert len(configured_jobs) == len(actual_jobs)
    super_handle.assert_called_once()


def test_register_cron_jobs__missing_keys():
    with pytest.raises(TypeError, match="is missing cron_string"):
        register_cron_jobs({"test": {"func": "test"}}, "short")
