import os
import re
import xml.etree.ElementTree as ET
from datetime import datetime

from cumulusci.utils import elementtree_parse_file
from django.core.files.base import ContentFile

from metaci.testresults.models import TestClass, TestMethod, TestResult, TestResultAsset

STATS_MAP = {
    "email_invocations": "Number of Email Invocations",
    "soql_queries": "Number of SOQL queries",
    "future_calls": "Number of future calls",
    "dml_rows": "Number of DML rows",
    "cpu_time": "Maximum CPU time",
    "query_rows": "Number of query rows",
    "dml_statements": "Number of DML statements",
    "mobile_apex_push": "Number of Mobile Apex push calls",
    "heap_size": "Maximum heap size",
    "sosl_queries": "Number of SOSL queries",
    "queueable_jobs": "Number of queueable jobs added to the queue",
    "callouts": "Number of callouts",
    "test_email_invocations": "TESTING_LIMITS: Number of Email Invocations",
    "test_soql_queries": "TESTING_LIMITS: Number of SOQL queries",
    "test_future_calls": "TESTING_LIMITS: Number of future calls",
    "test_dml_rows": "TESTING_LIMITS: Number of DML rows",
    "test_cpu_time": "TESTING_LIMITS: Maximum CPU time",
    "test_query_rows": "TESTING_LIMITS: Number of query rows",
    "test_dml_statements": "TESTING_LIMITS: Number of DML statements",
    "test_mobile_apex_push": "TESTING_LIMITS: Number of Mobile Apex push calls",
    "test_heap_size": "TESTING_LIMITS: Maximum heap size",
    "test_sosl_queries": "TESTING_LIMITS: Number of SOSL queries",
    "test_queueable_jobs": "TESTING_LIMITS: Number of queueable jobs added to the queue",
    "test_callouts": "TESTING_LIMITS: Number of callouts",
}

LIMIT_TYPES = (
    "email_invocations",
    "soql_queries",
    "future_calls",
    "dml_rows",
    "cpu_time",
    "query_rows",
    "dml_statements",
    "mobile_apex_push",
    "heap_size",
    "sosl_queries",
    "queueable_jobs",
    "callouts",
)


def import_test_results(build_flow, results, test_type):
    classes = {}
    methods = {}

    for result in results:
        class_and_method = "%s.%s" % (result["ClassName"], result["Method"])

        testclass = classes.get(result["ClassName"], None)
        if not testclass:
            testclass, created = TestClass.objects.get_or_create(
                name=result["ClassName"],
                repo=build_flow.build.repo,
                test_type=test_type,
            )
            classes[result["ClassName"]] = testclass

        method = methods.get(class_and_method, None)
        if not method:
            method, created = TestMethod.objects.get_or_create(
                testclass=testclass, name=result["Method"]
            )
            methods[result["Method"]] = method

        duration = None
        if (
            "Stats" in result
            and result["Stats"]
            and "duration" in result["Stats"]
            and result["Stats"]["duration"]
        ):
            duration = result["Stats"]["duration"]

        testresult = TestResult(
            build_flow=build_flow,
            method=method,
            duration=duration,
            outcome=result["Outcome"],
            stacktrace=result["StackTrace"],
            message=result["Message"],
            source_file=result["SourceFile"],
        )
        populate_limit_fields(testresult, result["Stats"])
        testresult.save()

    return build_flow


def populate_limit_fields(testresult, code_unit):
    for limit_type in LIMIT_TYPES:
        try:
            test_used = code_unit[STATS_MAP["test_%s" % limit_type]]["used"]
            test_allowed = code_unit[STATS_MAP["test_%s" % limit_type]]["allowed"]

            test_percent = None

            if test_used is not None and test_allowed:
                test_percent = (test_used * 100) / test_allowed

            setattr(testresult, "test_%s_used" % limit_type, test_used)
            setattr(testresult, "test_%s_allowed" % limit_type, test_allowed)
            setattr(testresult, "test_%s_percent" % limit_type, test_percent)
        except KeyError:
            continue

    worst_limit_test = None
    worst_limit_test_percent = None

    for limit_type in LIMIT_TYPES:
        percent_test = getattr(testresult, "test_%s_percent" % limit_type)

        if percent_test is None:
            continue
        if worst_limit_test_percent is None:
            worst_limit_test = "test_%s_percent" % limit_type
            worst_limit_test_percent = percent_test
        elif percent_test > worst_limit_test_percent:
            worst_limit_test = "test_%s_percent" % limit_type
            worst_limit_test_percent = percent_test

    testresult.worst_limit = worst_limit_test
    testresult.worst_limit_percent = worst_limit_test_percent
    testresult.worst_limit_test = worst_limit_test
    testresult.worst_limit_test_percent = worst_limit_test_percent


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


def get_robot_tests(root, elem, parents=[]):
    tests = []
    has_children = False
    for child in elem:
        if child.tag == "suite":
            has_children = True
            parents.append(child)
            tests += get_robot_tests(root, child, list(parents))
            parents = parents[:-1]

    if not has_children:
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
            status = test.find("status")
            test_info = {
                "suite": suite,
                "name": test.attrib["name"],
                "elem": test,
                "status": "Pass" if status.attrib["status"] == "PASS" else "Fail",
                "screenshots": [],
            }
            start = datetime.strptime(status.attrib["starttime"], "%Y%m%d %H:%M:%S.%f")
            end = datetime.strptime(status.attrib["endtime"], "%Y%m%d %H:%M:%S.%f")
            delta = end - start

            # Process screenshots
            test_info["screenshots"] = find_screenshots(test)
            test_info["duration"] = float(
                "{}.{}".format(delta.seconds, delta.microseconds)
            )
            test_info["xml"] = render_robot_test_xml(root, test_info)
            tests.append(test_info)

    return tests


def find_screenshots(root):
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
