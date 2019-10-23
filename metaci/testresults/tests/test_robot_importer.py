from pathlib import PurePath

import pytest
from django.test import TestCase

from metaci.conftest import BuildFlowFactory
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
        assert test_results[0].duration == 71.008

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
