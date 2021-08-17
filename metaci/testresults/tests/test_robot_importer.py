import fnmatch
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from pathlib import Path, PurePath
from shutil import copyfile
from unittest import mock

import pytest
import responses
from cumulusci.utils import elementtree_parse_file, temporary_dir
from django.conf import settings
from django.utils import timezone

from metaci.build.exceptions import BuildError
from metaci.build.models import BuildFlowAsset
from metaci.build.tests.test_flows import TEST_ROBOT_OUTPUT_FILES
from metaci.conftest import FlowTaskFactory
from metaci.testresults import models, robot_importer


@pytest.mark.django_db
def test_invalid_test_result_filepath():
    with pytest.raises(BuildError):
        robot_importer.import_robot_test_results(mock.Mock, "invalid/file/path")


@pytest.mark.django_db
def test_nested_suites():
    with temporary_dir() as output_dir:
        copyfile(
            TEST_ROBOT_OUTPUT_FILES / "robot_with_nested_suites.xml",
            Path(output_dir) / "output.xml",
        )

        flowtask = FlowTaskFactory()
        robot_importer.import_robot_test_results(flowtask, output_dir)

    assert models.TestResult.objects.all(), "Test results should have been created"
    test_result = models.TestResult.objects.get(method__name__contains="AAAAA")
    assert test_result.duration == 0.25
    assert test_result.method.name == "AAAAA Test Set Login Url"
    assert test_result.method.testclass.name == "Nested/Cumulusci/Base"


@pytest.mark.django_db
def test_basic_parsing():
    with temporary_dir() as output_dir:
        copyfile(
            TEST_ROBOT_OUTPUT_FILES / "robot_1.xml",
            Path(output_dir) / "output.xml",
        )

        robot_importer.import_robot_test_results(FlowTaskFactory(), output_dir)

    test_results = models.TestResult.objects.filter(method__name="FakeTestResult")
    assert test_results


@pytest.mark.django_db
def test_duration_calculations():
    with temporary_dir() as output_dir:
        copyfile(
            TEST_ROBOT_OUTPUT_FILES / "robot_with_setup_teardown.xml",
            Path(output_dir) / "output.xml",
        )
        robot_importer.import_robot_test_results(FlowTaskFactory(), output_dir)

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

    with temporary_dir() as output_dir:
        output_dir = Path(output_dir)
        copyfile(
            TEST_ROBOT_OUTPUT_FILES / "robot_with_setup_teardown.xml",
            output_dir / "output.xml",
        )
        output_xml_mtime = timezone.make_aware(
            datetime.fromtimestamp(output_dir.stat().st_mtime)
        )
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

        robot_importer.import_robot_test_results(flowtask, output_dir)

    for result in models.TestResult.objects.all():
        assert result.task is not None
        assert result.task.stepnum == "2"


@pytest.mark.django_db
def test_import_all_tests():
    """Verifies that we import all tests in a suite"""
    with temporary_dir() as output_dir:
        copyfile(
            TEST_ROBOT_OUTPUT_FILES / "robot_with_failures.xml",
            Path(output_dir) / "output.xml",
        )
        robot_importer.import_robot_test_results(FlowTaskFactory(), output_dir)

    failing_test_results = models.TestResult.objects.filter(outcome="Fail")
    passing_test_results = models.TestResult.objects.filter(outcome="Pass")
    assert len(failing_test_results) == 3
    assert len(passing_test_results) == 1


@pytest.mark.django_db
def test_field_keyword_and_message():
    """Verify that the keyword and message fields are populated"""
    with temporary_dir() as output_dir:
        copyfile(
            TEST_ROBOT_OUTPUT_FILES / "robot_with_failures.xml",
            Path(output_dir) / "output.xml",
        )
        robot_importer.import_robot_test_results(FlowTaskFactory(), output_dir)

    test_result = models.TestResult.objects.get(method__name="Failing test 1")
    assert test_result.message == "Danger, Will Robinson!"
    assert test_result.robot_keyword == "Keyword with failure"


@pytest.mark.django_db
def test_field_keyword_and_message_nested_keywords():
    """Verify that the keyword and message fields are set when failure is in a nested keyword"""
    with temporary_dir() as output_dir:
        copyfile(
            TEST_ROBOT_OUTPUT_FILES / "robot_with_failures.xml",
            Path(output_dir) / "output.xml",
        )
        robot_importer.import_robot_test_results(FlowTaskFactory(), output_dir)

    test_result = models.TestResult.objects.get(method__name="Failing test 2")
    assert test_result.message == "I'm sorry, Dave. I'm afraid I can't do that."
    assert test_result.robot_keyword == "Keyword which calls a failing keyword"


@pytest.mark.django_db
def test_field_keyword_and_message_passing_test():
    """Verify that the failing_keyword field is set correctly for passing tests"""
    with temporary_dir() as output_dir:
        copyfile(
            TEST_ROBOT_OUTPUT_FILES / "robot_with_failures.xml",
            Path(output_dir) / "output.xml",
        )
        robot_importer.import_robot_test_results(FlowTaskFactory(), output_dir)

    test_result = models.TestResult.objects.get(method__name="Passing test")
    assert test_result.message == "Life is good, yo."
    assert test_result.robot_keyword is None


@pytest.mark.django_db
def test_import_robot_tags():
    """Verify that we can store lots of tags

    For a while we had a hard limit of 80 characters for the string of
    tags. We've since removed that limit, and this test verifies that
    we can not only store tags, but store more than 80 characters
    worth of tags.

    """
    with temporary_dir() as output_dir:
        copyfile(
            TEST_ROBOT_OUTPUT_FILES / "robot_1.xml",
            Path(output_dir) / "output.xml",
        )
        robot_importer.import_robot_test_results(FlowTaskFactory(), output_dir)
    test_results = models.TestResult.objects.filter(method__name="FakeTestResult")
    actual_tags = test_results[0].robot_tags
    expected_tags = ",".join(
        (
            "Bender",
            "Bishop",
            "C-3PO",
            "Curiosity",
            "Huey Dewey and Louie",
            "Johnny 5",
            "Optimus Prime",
            "Perserverance",
            "R2-D2",
            "Robby",
            "Rosie",
            "T-1000",
            "The Iron Giant",
            "WALL-E",
        )
    )
    assert actual_tags == expected_tags


@pytest.mark.django_db
def test_execution_errors():
    """Verify pre-test execution errors are imported

    If robot has errors before the first test runs (eg: import
    errors) these errors were being thrown away. This test verifies
    that execution errors appear in imported test results.
    """
    with temporary_dir() as output_dir:
        copyfile(
            TEST_ROBOT_OUTPUT_FILES / "robot_with_import_errors.xml",
            Path(output_dir) / "output.xml",
        )
        robot_importer.import_robot_test_results(FlowTaskFactory(), output_dir)

    test_result = models.TestResult.objects.last()
    root = ET.fromstring(test_result.robot_xml)
    msg_elements = root.findall("./errors/msg")
    error_messages = [element.text for element in msg_elements]

    expected_error_messages = [
        # note: these are glob patterns, not regexes
        "Error in file '*' on line 2: Library setting requires value.",
        "Error in file '*' on line 3: Resource setting requires value.",
    ]
    assert len(error_messages) == len(expected_error_messages)
    for pattern in expected_error_messages:
        assert len(fnmatch.filter(error_messages, pattern)) == 1


@pytest.mark.django_db
def test_screenshots_generated():
    """Verify that screenshots were created properly.
    For the robot_screenshot.xml output file, there should be:
    * A BuildFlowAsset created for the output.xml file
    * A BuildFlowAsset created for the screenshot taken during suite setup
    * A TestResultAsset created for the 'Via UI' robot test
    """
    with temporary_dir() as output_dir:
        output_dir = Path(output_dir)
        copyfile(
            TEST_ROBOT_OUTPUT_FILES / "robot_screenshots.xml",
            output_dir / "output.xml",
        )
        open(output_dir / "selenium-screenshot-1.png", mode="w+")
        open(output_dir / "selenium-screenshot-2.png", mode="w+")

        flowtask = FlowTaskFactory()
        robot_importer.import_robot_test_results(flowtask, output_dir)

        # output.xml asset created
        assert 1 == BuildFlowAsset.objects.filter(category="robot-output").count()
        # suite setup screenshot assets created
        assert 1 == BuildFlowAsset.objects.filter(category="robot-screenshot").count()
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


@pytest.mark.django_db
def test_import_perf_results():
    with temporary_dir() as output_dir:
        copyfile(
            TEST_ROBOT_OUTPUT_FILES / "output_with_elapsed_times.xml",
            Path(output_dir) / "output.xml",
        )
        robot_importer.import_robot_test_results(FlowTaskFactory(), output_dir)
        assert models.TestResult.objects.all(), "Test results should have been created"
    test_result = models.TestResult.objects.all()
    durations = {x.method.name: x.duration for x in test_result}
    assert durations["Test Elapsed Time For Last Record"]
    for name, value in [
        ("Test Elapsed Time For Last Record", 278818780.0),
        ("Test Perf Set Elapsed Time", 11655.9),
        ("Test Perf Set Elapsed Time Twice", 53.0),
        ("Test Perf Set Elapsed Time String", 18000.0),
        ("Test Perf Measure Elapsed", 1.0),
        ("Set Time and Also Metric", 0.0),
    ]:
        assert durations[name] == value


@responses.activate
@pytest.mark.django_db
def test_gus_bus_test_manager(mocker):
    """Verifies that we import all tests in a suite"""
    mocker.patch(
        "metaci.testresults.robot_importer.settings",
        METACI_RELEASE_WEBHOOK_URL="https://webhook",
        METACI_RELEASE_WEBHOOK_ISSUER="MetaCI",
        METACI_RELEASE_WEBHOOK_AUTH_KEY="test",
    )
    mocker.patch(
        "metaci.build.flows.settings",
        RESULT_EXPORT_ENABLED=True,
    )
    mocker.patch(
        "metaci.testresults.tests.test_robot_importer.settings",
        METACI_RELEASE_WEBHOOK_URL="https://webhook",
    )
    flow_task = FlowTaskFactory()
    with temporary_dir() as output_dir:
        copyfile(
            TEST_ROBOT_OUTPUT_FILES / "robot_with_failures.xml",
            Path(output_dir) / "output.xml",
        )
        robot_importer.import_robot_test_results(flow_task, output_dir)
        responses.add(
            "POST",
            f"{settings.METACI_RELEASE_WEBHOOK_URL}/test-results/",
            json={
                "success": "True",
                "id": "123",
            },  # why does a boolean give  raise TypeError("Expected a string value")
        )
        assert robot_importer.export_robot_test_results(FlowTaskFactory()) is None
        assert len(responses.calls) == 1
        assert responses.calls[0].request.url == "https://webhook/test-results/"


@responses.activate
@pytest.mark.django_db
def test_gus_bus_test_manager_failure(mocker):
    """Verifies that we import all tests in a suite"""
    mocker.patch(
        "metaci.testresults.robot_importer.settings",
        METACI_RELEASE_WEBHOOK_URL="https://webhook",
        METACI_RELEASE_WEBHOOK_ISSUER="MetaCI",
        METACI_RELEASE_WEBHOOK_AUTH_KEY="test",
    )
    mocker.patch(
        "metaci.build.flows.settings",
        RESULT_EXPORT_ENABLED=True,
    )
    mocker.patch(
        "metaci.testresults.tests.test_robot_importer.settings",
        METACI_RELEASE_WEBHOOK_URL="https://webhook",
    )
    with pytest.raises(Exception):
        flow_task = FlowTaskFactory()
        with temporary_dir() as output_dir:
            copyfile(
                TEST_ROBOT_OUTPUT_FILES / "robot_with_failures.xml",
                Path(output_dir) / "output.xml",
            )
            robot_importer.import_robot_test_results(flow_task, output_dir)
            responses.add(
                "POST",
                f"{settings.METACI_RELEASE_WEBHOOK_URL}/test-results/",
                json={
                    "success": "",
                    "errors": ["error goes here"],
                },  # Boolean value will raise TypeError("Expected a string value") in CI tests.
            )
            robot_importer.export_robot_test_results(FlowTaskFactory())


@responses.activate
@pytest.mark.django_db
def test_gus_bus_test_manager_no_flowtask(mocker):
    """Verifies that we import all tests in a suite"""
    mocker.patch(
        "metaci.testresults.robot_importer.settings",
        METACI_RELEASE_WEBHOOK_URL="https://webhook",
        METACI_RELEASE_WEBHOOK_ISSUER="MetaCI",
        METACI_RELEASE_WEBHOOK_AUTH_KEY="test",
    )
    mocker.patch(
        "metaci.build.flows.settings",
        RESULT_EXPORT_ENABLED=True,
    )
    mocker.patch(
        "metaci.testresults.tests.test_robot_importer.settings",
        METACI_RELEASE_WEBHOOK_URL="https://webhook",
    )
    with temporary_dir() as output_dir:
        copyfile(
            TEST_ROBOT_OUTPUT_FILES / "robot_with_failures.xml",
            Path(output_dir) / "output.xml",
        )
        robot_importer.import_robot_test_results(FlowTaskFactory(), output_dir)

        assert robot_importer.export_robot_test_results(None) is None
        assert len(responses.calls) == 0
