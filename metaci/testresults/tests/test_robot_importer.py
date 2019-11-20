from datetime import datetime, timedelta
from pathlib import Path, PurePath

import pytest
from django.test import TestCase
from django.utils import timezone

from metaci.conftest import BuildFlowFactory, FlowTaskFactory
from metaci.testresults import models, robot_importer


@pytest.mark.django_db
class RobotImporterTestCase(TestCase):
    def test_nested_suites(self):
        buildflow = BuildFlowFactory()
        path = PurePath(__file__).parent / "robot_with_nested_suites.xml"
        robot_importer.import_robot_test_results(buildflow, path)
        assert models.TestResult.objects.all(), "Test results should have been created"
        test_result = models.TestResult.objects.get(method__name__contains="AAAAA")
        assert test_result.duration == 0.25
        assert test_result.method.name == "AAAAA Test Set Login Url"
        assert test_result.method.testclass.name == "Nested/Cumulusci/Base"

    def test_basic_parsing(self):
        buildflow = BuildFlowFactory()
        path = PurePath(__file__).parent / "robot_1.xml"
        robot_importer.import_robot_test_results(buildflow, path)
        test_results = models.TestResult.objects.filter(method__name="FakeTestResult")
        assert test_results

    def test_duration_calculations(self):
        buildflow = BuildFlowFactory()
        path = PurePath(__file__).parent / "robot_with_setup_teardown.xml"
        robot_importer.import_robot_test_results(buildflow, path)
        correct = 14.002
        duration = models.TestResult.objects.get(
            method__name="FakeTestResult2"
        ).duration
        assert duration == correct
        correct = 15.001
        duration = models.TestResult.objects.get(
            method__name="FakeTestResult_setup_no_teardown"
        ).duration
        assert duration == correct
        correct = 20.002
        duration = models.TestResult.objects.get(
            method__name="FakeTestResult_teardown_no_setup"
        ).duration
        assert duration == correct

    def test_robot_task_attribute(self):
        """verify that the robot_task attribute of a TestResult has been
        set for a robot test result

        The importer uses the timestamp of the output file to figure
        out which task generated the file. It then uses the options
        of this task to generate the log files.

        This test creates a few FlowTask objects where one has a start
        time and end time that encompases the mtime of the output
        file. That task should get saved with the test result.
        """

        path = Path(__file__).parent / "robot_with_setup_teardown.xml"
        output_xml_mtime = timezone.make_aware(
            datetime.fromtimestamp(path.stat().st_mtime)
        )
        buildflow = BuildFlowFactory()
        time_offsets = ((-60, -30), (-29, +1), (+2, +10))
        FlowTaskFactory.reset_sequence(value=1)
        for (start_offset, end_offset) in time_offsets:
            time_start = output_xml_mtime + timedelta(seconds=start_offset)
            time_end = output_xml_mtime + timedelta(seconds=end_offset)
            task = FlowTaskFactory(
                build_flow=buildflow, time_start=time_start, time_end=time_end,
            )
            task.save()

        robot_importer.import_robot_test_results(buildflow, path)
        for result in models.TestResult.objects.all():
            assert result.robot_task is not None
            assert result.robot_task.stepnum == "2."
