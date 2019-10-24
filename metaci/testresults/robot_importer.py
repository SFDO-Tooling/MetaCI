import os
import re
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta

from cumulusci.utils import elementtree_parse_file
from django.core.files.base import ContentFile

from metaci.testresults.models import TestClass, TestMethod, TestResult, TestResultAsset


def import_robot_test_results(build_flow, path):
    # import is here to avoid import cycle
    from metaci.build.models import BuildFlowAsset

    classes = {}
    methods = {}

    with open(path, "rb") as f:
        asset = BuildFlowAsset(
            build_flow=build_flow,
            asset=ContentFile(f.read(), "output.xml"),
            category="robot-output",
        )
        asset.save()

    suite_screenshots = {}
    for result in parse_robot_output(path):
        class_and_method = "{}.{}".format(result["suite"]["name"], result["name"])

        testclass = classes.get(result["suite"]["name"], None)
        if not testclass:
            testclass, created = TestClass.objects.get_or_create(
                name=result["suite"]["name"],
                repo=build_flow.build.repo,
                test_type="Robot",
            )
            classes[result["suite"]["name"]] = testclass

        # Attach suite screenshots to buildflow
        dirname = os.path.dirname(path)
        for screenshot in result["suite"]["screenshots"]:
            if screenshot in suite_screenshots:
                continue
            screenshot_path = screenshot
            if dirname:
                screenshot_path = "{}/{}".format(dirname, screenshot)
            with open(screenshot_path, "rb") as f:
                asset = BuildFlowAsset(
                    build_flow=build_flow,
                    asset=ContentFile(f.read(), screenshot),
                    category="robot-screenshot",
                )
                asset.save()
                suite_screenshots[screenshot] = asset.id
            os.remove(screenshot_path)

        method = methods.get(class_and_method, None)
        if not method:
            method, created = TestMethod.objects.get_or_create(
                testclass=testclass, name=result["name"]
            )
            methods[class_and_method] = method

        testresult = TestResult(
            build_flow=build_flow,
            method=method,
            duration=result["duration"],
            outcome=result["status"],
            source_file=result["suite"]["file"],
            robot_xml=result["xml"],
        )
        testresult.save()

        # attach test case screenshots to test result
        if result["screenshots"] or suite_screenshots:
            for screenshot in result["screenshots"]:
                screenshot_path = screenshot
                if dirname:
                    screenshot_path = "{}/{}".format(dirname, screenshot)
                with open(screenshot_path, "rb") as f:
                    asset = TestResultAsset(
                        result=testresult, asset=ContentFile(f.read(), screenshot)
                    )
                    asset.save()
                    # replace references to local files with TestResultAsset ids
                    testresult.robot_xml = testresult.robot_xml.replace(
                        '"{}"'.format(screenshot), '"asset://{}"'.format(asset.id)
                    )
                os.remove(screenshot_path)
            # replace references to suite screenshots with BuildFlowAsset ids
            for screenshot, asset_id in suite_screenshots.items():
                testresult.robot_xml = testresult.robot_xml.replace(
                    '"{}"'.format(screenshot), '"buildflowasset://{}"'.format(asset_id)
                )
            testresult.save()


def parse_robot_output(path):
    """ Parses a robotframework output.xml file into individual test xml files """

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

    if not has_children_suites:
        suite_file = elem.attrib["source"].replace(os.getcwd(), "")
        setup = elem.find("kw[@type='setup']")
        teardown = elem.find("kw[@type='teardown']")
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
    setup = test.find("kw[@type='setup']")
    teardown = test.find("kw[@type='teardown']")
    zero = timedelta(seconds=0)
    setup_time = _robot_duration(setup.find("status")) if setup else zero
    teardown_time = _robot_duration(teardown.find("status")) if teardown else zero

    test_info = {
        "suite": suite,
        "name": test.attrib["name"],
        "elem": test,
        "status": "Pass" if status.attrib["status"] == "PASS" else "Fail",
        "screenshots": [],
    }
    delta = _robot_duration(status)
    duration = delta - (setup_time + teardown_time)

    # Process screenshots
    test_info["screenshots"] = find_screenshots(test)
    test_info["duration"] = duration.total_seconds()

    test_info["xml"] = render_robot_test_xml(root, test_info)
    return test_info


def find_screenshots(root):
    if root is None:
        return []
    screenshots = []
    for msg in root.findall(".//msg[@html='yes']"):
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
    test_xml = ET.tostring(testroot, encoding="unicode")
    return re.sub(r"sid=.*<", "sid=MASKED<", test_xml)
