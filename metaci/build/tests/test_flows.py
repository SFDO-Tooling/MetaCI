from pathlib import Path, PurePath
from unittest import mock

import pytest
from cumulusci.core.flowrunner import StepResult, StepSpec
from cumulusci.tasks.robotframework.robotframework import Robot

from metaci.build.flows import MetaCIFlowCallback
from metaci.build.models import BuildFlowAsset, FlowTask
from metaci.fixtures.factories import BuildFlowFactory
from metaci.testresults.models import TestMethod, TestResult, TestResultAsset


@pytest.fixture
def get_spec():
    def func(num, name="test-task", cls=None):
        return StepSpec(
            step_num=num,
            task_name=name,
            task_config=mock.Mock(),
            task_class=cls,
            project_config=mock.Mock(),
        )

    return func


@pytest.mark.django_db
def test_post_task__result_complete(get_spec):
    step_spec = get_spec("1")
    step_result = StepResult(
        step_num="1",
        task_name="test-task",
        path="test-task",
        result="something",
        return_values={},
        exception=None,
    )

    build_flow = BuildFlowFactory()
    metaci_callbacks = MetaCIFlowCallback(build_flow.id)
    metaci_callbacks.post_task(step_spec, step_result)

    ft = FlowTask.objects.get(build_flow=build_flow)
    assert ft.status == "complete"


@pytest.mark.django_db
def test_post_task__result_has_exception(get_spec):
    step_spec = get_spec("1")
    step_result = StepResult(
        step_num="1",
        task_name="test-task",
        path="test-task",
        result="something",
        return_values={},
        exception=TestException,
    )

    build_flow = BuildFlowFactory()
    metaci_callbacks = MetaCIFlowCallback(build_flow.id)
    metaci_callbacks.post_task(step_spec, step_result)

    flowtask = FlowTask.objects.get(build_flow=build_flow)
    assert flowtask.exception == str(TestException.__class__)
    assert flowtask.status == "error"


@pytest.mark.django_db
def test_post_task__multiple_robot_output_files(get_spec):
    path = PurePath(__file__).parent.parent.parent / "testresults/tests"
    step_spec = get_spec("1", name="Robot", cls=Robot)
    step_result = StepResult(
        step_num="1",
        task_name="Robot",
        path="Robot",
        result="something",
        return_values={"robot_outputdir": str(path / "robot_1.xml")},
        exception=None,
    )

    build_flow = BuildFlowFactory()
    metaci_callbacks = MetaCIFlowCallback(build_flow.id)
    metaci_callbacks.post_task(step_spec, step_result)

    # For output_1 we should have a single BuildFlowAsset,
    # a single TestResult, and no TestResultAssets (screenshots)
    assert (
        1
        == BuildFlowAsset.objects.filter(
            category="robot-output", build_flow=build_flow
        ).count()
    )
    assert 1 == TestResult.objects.all().count()
    assert 0 == TestResultAsset.objects.all().count()

    step_spec = get_spec("2", name="Robot", cls=Robot)
    step_result = StepResult(
        step_num="2",
        task_name="Robot",
        path="Robot",
        result="something",
        return_values={"robot_outputdir": str(path / "robot_screenshots.xml")},
        exception=None,
    )

    with open(Path(path / "selenium-screenshot-1.png"), mode="w+"):
        with open(Path(path / "selenium-screenshot-2.png"), mode="w+"):
            metaci_callbacks.post_task(step_spec, step_result)
            # There should now be two output files for the buildflow
            assert (
                2
                == BuildFlowAsset.objects.filter(
                    category="robot-output", build_flow=build_flow
                ).count()
            )
            # There should be a screenshot created during suite setup
            assert (
                1
                == BuildFlowAsset.objects.filter(category="robot-screenshot-1").count()
            )
            # No screenshots created for 'Via API' test
            tr_method = TestMethod.objects.get(name="Via API")
            test_api = TestResult.objects.get(method=tr_method)
            assert 0 == test_api.assets.count()

            # One screenshot created for 'Via UI' test
            tr_method = TestMethod.objects.get(name="Via UI")
            test_ui = TestResult.objects.get(method=tr_method)
            assert 1 == test_ui.assets.count()

    # Three tests total between the two output files
    assert 3 == TestMethod.objects.all().count()


class TestException(Exception):
    pass
