from pathlib import PurePath

import pytest
from django.test import TestCase

from metaci.conftest import BuildFlowFactory
from metaci.testresults import models, robot_importer


@pytest.mark.django_db
class RobotImporterTestCase(TestCase):
    def setUp(self):
        pass

    def test_nested_suites(self):
        buildflow = BuildFlowFactory()
        path = PurePath(__file__).parent / "robot_with_nested_suites.xml"
        robot_importer.import_robot_test_results(buildflow, path)
        assert models.TestResult.objects.all(), "Test results should have been created"

    def test_basic_parsing(self):
        buildflow = BuildFlowFactory()
        path = PurePath(__file__).parent / "robot_1.xml"
        robot_importer.import_robot_test_results(buildflow, path)
        test_results = models.TestResult.objects.filter(method__name="FakeTestResult")
        assert test_results[0].duration == 71.008

    def test_duration_calcuations(self):
        buildflow = BuildFlowFactory()
        path = PurePath(__file__).parent / "robot_with_setup_teardown.xml"
        robot_importer.import_robot_test_results(buildflow, path)
        res = 14.002
        assert (
            models.TestResult.objects.filter(method__name="FakeTestResult2")[0].duration
            == res
        )
