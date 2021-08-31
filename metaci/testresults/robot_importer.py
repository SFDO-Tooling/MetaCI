import logging
import os
import re
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from pathlib import Path
from typing import List

import requests
import robot
from cumulusci.utils import elementtree_parse_file
from cumulusci.utils.xml.robot_xml import pattern as ELAPSED_TIME_PATTERN
from django.conf import settings
from django.core.files.base import ContentFile

from metaci.build.exceptions import BuildError
from metaci.release.utils import jwt_for_webhook
from metaci.testresults.models import TestClass, TestMethod, TestResult, TestResultAsset

logger = logging.getLogger(__name__)


def import_robot_test_results(flowtask, results_dir: str) -> List:
    """Given a flowtask for a robot task, and a path to the
    test results output file:

    (1) Parse the test result output file
    (2) Create the following records and save them to the DB:
        (a) A BuildFlowAsset of the output.xml file associated with the build_flow
        (b) A TestClass for each class in the output file (if they don't already exist)
        (c) A BuildFlowAsset record for any screenshots created during test setup/teardown.
        (d) TestMethod for each method in the class (if they don't already exist)
        (e) TestResult associated with the BuildFlow, TestMethod, and FlowTask
        (f) TestResultAsset for any screenshots in the TestResult

    @param1 (FlowTask) The flowtask associated with the robot task
    @param1 (str) The filepath to the robot results
    """
    results = []
    results_dir = Path(results_dir)
    results_file = results_dir / "output.xml"  # robot output filename

    if not results_dir.is_dir():
        raise BuildError(f"Robot results directory is not a directory: {results_dir}")
    if not results_file.is_file():
        raise BuildError(f"File does not exist: {results_file}")

    # import is here to avoid import cycle
    from metaci.build.models import BuildFlowAsset

    with open(results_file, "rb") as f:
        asset = BuildFlowAsset(
            build_flow=flowtask.build_flow,
            asset=ContentFile(f.read(), f"step-{flowtask.stepnum}-output.xml"),
            category="robot-output",
        )
        asset.save()

    classes = {}
    methods = {}
    suite_screenshots = {}
    for result in parse_robot_output(results_file):
        testclass = classes.get(result["suite"]["name"], None)
        if not testclass:
            testclass, created = TestClass.objects.get_or_create(
                name=result["suite"]["name"],
                repo=flowtask.build_flow.build.repo,
                test_type="Robot",
            )
            classes[result["suite"]["name"]] = testclass

        # Create screenshot assets for corresponding BuildFlow
        # These screenshots are generated during robot test suite setup/teardown
        for i, screenshot in enumerate(result["suite"]["screenshots"]):

            if screenshot in suite_screenshots:
                continue

            screenshot_path = results_dir / screenshot

            with open(screenshot_path, "rb") as f:
                asset = BuildFlowAsset(
                    build_flow=flowtask.build_flow,
                    asset=ContentFile(
                        f.read(), f"step-{flowtask.stepnum}-{screenshot}"
                    ),
                    category="robot-screenshot",
                )
                asset.save()
                suite_screenshots[screenshot] = asset.id
            screenshot_path.unlink()

        # Set TestMethod in `method` dict, and associate it
        # with the corresponding TestClass
        class_and_method = f"{result['suite']['name']}.{result['name']}"
        method = methods.get(class_and_method, None)
        if not method:
            method, created = TestMethod.objects.get_or_create(
                testclass=testclass, name=result["name"]
            )
            methods[class_and_method] = method

        # Create TestResult associated with the BuildFlow,
        # TestMethod, and FlowTask
        testresult = TestResult(
            build_flow=flowtask.build_flow,
            method=method,
            duration=result["duration"],
            outcome=result["status"],
            source_file=result["suite"]["file"],
            message=result["message"],
            robot_keyword=result["failing_keyword"],
            robot_xml=result["xml"],
            robot_tags=",".join(result["tags"]),
            task=flowtask,
        )
        testresult.save()

        # Attach test case screenshots to test result
        if result["screenshots"] or suite_screenshots:
            for screenshot in result["screenshots"]:
                screenshot_path = results_dir / screenshot
                with open(screenshot_path, "rb") as f:
                    asset = TestResultAsset(
                        result=testresult, asset=ContentFile(f.read(), screenshot)
                    )
                    asset.save()
                    # replace references to local files with TestResultAsset ids
                    testresult.robot_xml = testresult.robot_xml.replace(
                        f'"{screenshot}"', f'"asset://{asset.id}"'
                    )
                screenshot_path.unlink()
            # replace references to suite screenshots with BuildFlowAsset ids
            for screenshot, asset_id in suite_screenshots.items():
                testresult.robot_xml = testresult.robot_xml.replace(
                    f'"{screenshot}"', f'"buildflowasset://{asset_id}"'
                )

            testresult.save()
        results.append(
            {
                "name": result["name"],
                "group": result["suite"]["name"],
                "status": result["status"].capitalize(),
                "start_time": result["start_time"],
                "end_time": result["end_time"],
                "exception": result["message"],
                "tags": result["tags"],
                "doc": result["doc"],
            }
        )
    return results


def parse_robot_output(path):
    """Parses a robotframework output.xml file into individual test xml files"""
    tree = elementtree_parse_file(path)
    root = tree.getroot()
    return get_robot_tests(root, root)


def get_robot_tests(root, elem, parents=()):
    tests = []
    has_children_suites = False
    for child in elem:
        if child.tag == "suite":
            has_children_suites = True
            tests += get_robot_tests(root, child, parents + (child,))
    if not has_children_suites:  # base case of recursion
        suite_file = elem.attrib["source"].replace(os.getcwd(), "")
        setup = elem.find("kw[@type='SETUP']")
        teardown = elem.find("kw[@type='TEARDOWN']")
        suite = {
            "file": suite_file,
            "elem": elem,
            "name": "/".join([suite.attrib["name"] for suite in parents]),
            "setup": setup,
            "status": elem.find("status"),
            "teardown": teardown,
            "screenshots": find_screenshots(setup) + find_screenshots(teardown),
        }
        for test in elem.iter("test"):
            tests.append(parse_test(test, suite, root))
    return tests


def _parse_robot_time(timestring):
    return datetime.strptime(timestring, "%Y%m%d %H:%M:%S.%f")


def _robot_duration(status_element):
    start = _parse_robot_time(status_element.attrib["starttime"])
    end = _parse_robot_time(status_element.attrib["endtime"])
    return end - start


def parse_test(test, suite, root):
    status = test.find("status")
    doc = test.find("doc")
    setup = test.find("kw[@type='SETUP']")
    teardown = test.find("kw[@type='TEARDOWN']")
    zero = timedelta(seconds=0)
    setup_time = _robot_duration(setup.find("status")) if setup else zero
    teardown_time = _robot_duration(teardown.find("status")) if teardown else zero
    start_time = (
        _parse_robot_time(status.attrib["starttime"]).astimezone(None).isoformat()
    )
    end_time = _parse_robot_time(status.attrib["endtime"]).astimezone(None).isoformat()
    # I'm not 100% convinced this is what we want. It's great in the
    # normal case, but it's possible for a test to have multiple failing
    # keywords. We'll tackle that when it becomes an issue. For now,
    # we just grab the first failing keyword.
    keyword = None
    if status.attrib["status"] == "FAIL":
        failed_keyword_element = test.find("./kw/status[@status='FAIL']/..")
        if failed_keyword_element:
            keyword = failed_keyword_element.attrib.get("name")
            library = failed_keyword_element.attrib.get("library")
            if library:
                keyword = f"{library}.{keyword}"

    tags = sorted([tag.text for tag in test.iterfind("tag")])
    test_info = {
        "suite": suite,
        "name": test.attrib.get("name") or "<no name>",
        "elem": test,
        "doc": "" if doc is None else doc.text,
        # Note: robot status should always be PASS, FAIL, or SKIP, so
        # it's a simple transformation to become one of the values from
        # OUTCOME_CHOICES in testresults/choices.py
        "start_time": start_time,
        "end_time": end_time,
        "status": status.attrib["status"].capitalize(),
        "screenshots": [],
        "message": status.text,
        "failing_keyword": keyword,
        "tags": tags,
    }
    duration = duration_from_performance_keywords(test)
    if duration is not None:
        test_info["duration"] = duration
    else:
        delta = _robot_duration(status)
        duration = delta - (setup_time + teardown_time)
        test_info["duration"] = duration.total_seconds()

    # Process screenshots
    test_info["screenshots"] = find_screenshots(test)

    test_info["xml"] = render_robot_test_xml(root, test_info)
    return test_info


def duration_from_performance_keywords(test):
    """Try to find the tags injected by Robot performance testing keywords"""
    msgs = test.iter("msg")
    msg_patterns = (
        re.match(ELAPSED_TIME_PATTERN, msg.text.strip()) if msg.text else None
        for msg in msgs
    )
    matches = [match for match in msg_patterns if match]
    duration = None
    for match in matches:
        metric, value = match["metric"], float(match["value"])
        if metric == "elapsed_time":
            duration = value

    return duration


def find_screenshots(root):
    if root is None:
        return []
    screenshots = []
    for msg in root.findall(".//msg[@html='true']"):
        txt = "".join([text for text in msg.itertext()])
        for screenshot in re.findall(r'href="([\w.-]+)">', txt):
            screenshots.append(screenshot)
    return screenshots


def render_robot_test_xml(root, test):
    testroot = ET.Element(root.tag, root.attrib)
    suite_attrib = test["suite"]["elem"].attrib.copy()
    suite_attrib.update({"id": "s1", "name": test["suite"]["name"]})
    suite = ET.SubElement(
        testroot,
        "suite",
        {"id": "s1", "name": test["suite"]["name"], "source": test["suite"]["file"]},
    )
    if test["suite"]["setup"] is not None:
        suite.append(test["suite"]["setup"])
    suite.append(test["elem"])
    if test["suite"]["teardown"] is not None:
        suite.append(test["suite"]["teardown"])
    suite.append(test["suite"]["status"])

    # Append text execution errors, if any. These are errors that
    # happen outside of an individual test, such as problems importing
    # a library or resource file.
    execution_errors = root.find("errors")
    if execution_errors:
        testroot.append(execution_errors)

    test_xml = ET.tostring(testroot, encoding="unicode")
    return re.sub(r"sid=.*<", "sid=MASKED<", test_xml)


def export_robot_test_results(flowtask, test_results) -> None:
    """Sends robot test results to test-manager via api call to gus-bus."""
    if not settings.METACI_RELEASE_WEBHOOK_URL or not flowtask:
        return
    logger.info(
        f"Sending test results webhook for {flowtask.build_flow.build.get_external_url()} to {settings.METACI_RELEASE_WEBHOOK_URL}"
    )
    payload = {
        "build": {
            "name": flowtask.build_flow.build.plan.name,
            "branch_name": flowtask.build_flow.build.branch.name,
            "org": flowtask.build_flow.build.org.name,
            "number": flowtask.build_flow.build.id,
            "url": f"{flowtask.build_flow.build.get_external_url()}",
            "metadata": {
                "test_framework": f"Robotframework/{robot.__version__}",
                **flowtask.build_flow.build.repo.metadata,
            },
        },
        "tests": test_results,
    }

    token = jwt_for_webhook()
    response = requests.post(
        f"{settings.METACI_RELEASE_WEBHOOK_URL}/test-results",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )
    if response.status_code >= 400:
        raise Exception(response.text)
    result = response.json()

    if result["success"]:
        logger.info(
            f"Successfully sent test results to {settings.METACI_RELEASE_WEBHOOK_URL}/test-results"
        )
    else:
        msg = "\n".join(err["msg"] for err in result["errors"])
        raise Exception(f"Error while sending test-results webhook: {msg}")
