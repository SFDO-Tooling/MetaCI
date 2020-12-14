import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from pathlib import Path, PurePath
from unittest import mock

import pytest
from cumulusci.utils import elementtree_parse_file
from django.utils import timezone

from metaci.build.exceptions import BuildError
from metaci.build.models import BuildFlowAsset
from metaci.conftest import FlowTaskFactory
from metaci.fixtures.factories import BuildFlowFactory
from metaci.testresults import models, robot_importer


@pytest.mark.django_db
def test_invalid_test_result_filepath():
    with pytest.raises(BuildError):
        robot_importer.import_robot_test_results(mock.Mock, "invalid/file/path")


@pytest.mark.django_db
def test_nested_suites():
    flowtask = FlowTaskFactory()
    path = PurePath(__file__).parent / "robot_with_nested_suites.xml"

    robot_importer.import_robot_test_results(flowtask, path)
    assert models.TestResult.objects.all(), "Test results should have been created"
    test_result = models.TestResult.objects.get(method__name__contains="AAAAA")
    assert test_result.duration == 0.25
    assert test_result.method.name == "AAAAA Test Set Login Url"
    assert test_result.method.testclass.name == "Nested/Cumulusci/Base"


@pytest.mark.django_db
def test_basic_parsing():
    flowtask = FlowTaskFactory()
    path = PurePath(__file__).parent / "robot_1.xml"
    robot_importer.import_robot_test_results(flowtask, path)
    test_results = models.TestResult.objects.filter(method__name="FakeTestResult")
    assert test_results


@pytest.mark.django_db
def test_duration_calculations():
    flowtask = FlowTaskFactory()
    path = PurePath(__file__).parent / "robot_with_setup_teardown.xml"
    robot_importer.import_robot_test_results(flowtask, path)
    correct = 14.002
    duration = models.TestResult.objects.get(method__name="FakeTestResult2").duration
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


@pytest.mark.django_db
def test_field_robot_task():
    """verify that the task field of a TestResult has been
    set for a robot test result

    The importer uses the timestamp of the output file to figure
    out which task generated the file. It then uses the options
    of this task to generate the log files.

    This test creates a few FlowTask objects where one has a start
    time and end time that encompasses the mtime of the output
    file. That task should get saved with the test result.
    """

    path = Path(__file__).parent / "robot_with_setup_teardown.xml"
    output_xml_mtime = timezone.make_aware(datetime.fromtimestamp(path.stat().st_mtime))
    flowtask = FlowTaskFactory(stepnum=2)
    time_offsets = ((-60, -30), (-29, +1), (+2, +10))
    FlowTaskFactory.reset_sequence(value=1)
    for (start_offset, end_offset) in time_offsets:
        time_start = output_xml_mtime + timedelta(seconds=start_offset)
        time_end = output_xml_mtime + timedelta(seconds=end_offset)

        task = FlowTaskFactory(
            build_flow=flowtask.build_flow,
            time_start=time_start,
            time_end=time_end,
        )
        task.save()

    robot_importer.import_robot_test_results(flowtask, path)
    for result in models.TestResult.objects.all():
        assert result.task is not None
        assert result.task.stepnum == "2"


@pytest.mark.django_db
def test_import_all_tests():
    """Verifies that we import all tests in a suite"""
    flowtask = FlowTaskFactory()
    path = PurePath(__file__).parent / "robot_with_failures.xml"
    robot_importer.import_robot_test_results(flowtask, path)
    failing_test_results = models.TestResult.objects.filter(outcome="Fail")
    passing_test_results = models.TestResult.objects.filter(outcome="Pass")
    assert len(failing_test_results) == 3
    assert len(passing_test_results) == 1


@pytest.mark.django_db
def test_field_keyword_and_message():
    """Verify that the keyword and message fields are populated"""
    flowtask = FlowTaskFactory()
    path = PurePath(__file__).parent / "robot_with_failures.xml"
    robot_importer.import_robot_test_results(flowtask, path)

    test_result = models.TestResult.objects.get(method__name="Failing test 1")
    assert test_result.message == "Danger, Will Robinson!"
    assert test_result.robot_keyword == "Keyword with failure"


@pytest.mark.django_db
def test_field_keyword_and_message_nested_keywords():
    """Verify that the keyword and message fields are set when failure is in a nested keyword"""
    flowtask = FlowTaskFactory()
    path = PurePath(__file__).parent / "robot_with_failures.xml"
    robot_importer.import_robot_test_results(flowtask, path)

    test_result = models.TestResult.objects.get(method__name="Failing test 2")
    assert test_result.message == "I'm sorry, Dave. I'm afraid I can't do that."
    assert test_result.robot_keyword == "Keyword which calls a failing keyword"


@pytest.mark.django_db
def test_field_keyword_and_message_passing_test():
    """Verify that the failing_keyword field is set correctly for passing tests"""
    flowtask = FlowTaskFactory()
    path = PurePath(__file__).parent / "robot_with_failures.xml"
    robot_importer.import_robot_test_results(flowtask, path)

    test_result = models.TestResult.objects.get(method__name="Passing test")
    assert test_result.message == "Life is good, yo."
    assert test_result.robot_keyword is None


@pytest.mark.django_db
def test_import_robot_tags():
    """Verify that robot tags are added to the database"""
    flowtask = FlowTaskFactory()
    path = PurePath(__file__).parent / "robot_1.xml"
    robot_importer.import_robot_test_results(flowtask, path)
    test_results = models.TestResult.objects.filter(method__name="FakeTestResult")
    assert test_results[0].robot_tags == "tag with spaces,w-123456"


@pytest.mark.django_db
def test_execution_errors():
    """Verify pre-test execution errors are imported

    If robot has errors before the first test runs (eg: import
    errors) these errors were being thrown away. This test verifies
    that execution errors appear in imported test results.
    """
    flowtask = FlowTaskFactory()
    path = PurePath(__file__).parent / "robot_with_import_errors.xml"
    robot_importer.import_robot_test_results(flowtask, path)

    test_result = models.TestResult.objects.last()
    root = ET.fromstring(test_result.robot_xml)
    msg_elements = root.findall("./errors/msg")
    error_messages = [element.text for element in msg_elements]

    expected_error_messages = [
        "Error in file 'example.robot' on line 2: Library setting requires value.",
        "Error in file 'example.robot' on line 3: Resource setting requires value.",
    ]
    assert len(error_messages) == len(expected_error_messages)


@pytest.mark.django_db
def test_multiple_robot_tasks():
    """Verify that executing import_robot_test_results() with
    multiple Robot task outputfiles generates the expected records."""
    build_flow = BuildFlowFactory()
    flowtask1 = FlowTaskFactory(build_flow=build_flow)
    flowtask2 = FlowTaskFactory(build_flow=build_flow)
    path = PurePath(__file__).parent
    output_1 = path / "robot_1.xml"
    output_2 = path / "robot_screenshots.xml"
    ss_1_path = Path(path / "selenium-screenshot-1.png")
    ss_2_path = Path(path / "selenium-screenshot-2.png")

    robot_importer.import_robot_test_results(flowtask1, output_1)

    # For output_1 we should have a single BuildFlowAsset,
    # a single TestResult, and no TestResultAssets (screenshots)
    assert (
        1
        == BuildFlowAsset.objects.filter(
            category="robot-output", build_flow=build_flow
        ).count()
    )
    assert 1 == models.TestResult.objects.all().count()
    assert 0 == models.TestResultAsset.objects.all().count()

    with open(ss_1_path, mode="w+"):
        with open(ss_2_path, mode="w+"):
            robot_importer.import_robot_test_results(flowtask2, output_2)
            # There should now be two output files for the buildflow
            assert (
                2
                == BuildFlowAsset.objects.filter(
                    category="robot-output", build_flow=build_flow
                ).count()
            )
            # suite setup screenshot assets created
            assert (
                1
                == BuildFlowAsset.objects.filter(category="robot-screenshot-1").count()
            )
            # No screenshots created for 'Via API' test
            tr_method = models.TestMethod.objects.get(name="Via API")
            test_api = models.TestResult.objects.get(method=tr_method, task=flowtask2)
            assert 0 == test_api.assets.count()

            # One screenshot created for 'Via UI' test
            tr_method = models.TestMethod.objects.get(name="Via UI")
            test_ui = models.TestResult.objects.get(method=tr_method, task=flowtask2)
            assert 1 == test_ui.assets.count()

    # Three tests total between the two output files
    assert 3 == models.TestMethod.objects.all().count()


@pytest.mark.django_db
def test_screenshots_generated():
    """Verify that screenshots were created properly.
    For the robot_screenshot.xml output file, there should be:
    * A BuildFlowAsset created for the output.xml file
    * A BuildFlowAsset created for the screenshot taken during suite setup
    * A TestResultAsset created for the 'Via UI' robot test
    """
    flowtask = FlowTaskFactory()
    path = PurePath(__file__).parent
    robot_output = path / "robot_screenshots.xml"
    ss_1_path = Path(path / "selenium-screenshot-1.png")
    ss_2_path = Path(path / "selenium-screenshot-2.png")

    with open(ss_1_path, mode="w+"):
        with open(ss_2_path, mode="w+"):
            robot_importer.import_robot_test_results(flowtask, robot_output)
            # output.xml asset created
            assert 1 == BuildFlowAsset.objects.filter(category="robot-output").count()
            # suite setup screenshot assets created
            assert (
                1
                == BuildFlowAsset.objects.filter(category="robot-screenshot-1").count()
            )
            # No screenshots created for 'Via API' test
            tr_method = models.TestMethod.objects.get(name="Via API")
            test_api = models.TestResult.objects.get(method=tr_method, task=flowtask)
            assert 0 == test_api.assets.count()

            # One screenshot created for 'Via UI' test
            tr_method = models.TestMethod.objects.get(name="Via UI")
            test_ui = models.TestResult.objects.get(method=tr_method, task=flowtask)
            assert 1 == test_ui.assets.count()


@pytest.mark.django_db
def test_find_screenshots():
    path = PurePath(__file__).parent / "robot_screenshots.xml"
    tree = elementtree_parse_file(path)
    screenshots = robot_importer.find_screenshots(tree.getroot())
    assert len(screenshots) == 2
