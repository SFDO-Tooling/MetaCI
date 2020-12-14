import pytest
from unittest import mock
from pathlib import Path, PurePath

from cumulusci.core.flowrunner import StepSpec

from metaci.build.models import BuildFlow, BuildFlowAsset
from metaci.build.flows import MetaCIFlowCallback
from metaci.conftest import FlowTaskFactory
from metaci.fixtures.factories import BuildFlowFactory
from metaci.testresults.models import TestMethod, TestResult, TestResultAsset


@pytest.mark.django_db
def test_post_flow__multiple_robot_output_files():
    build_flow = BuildFlowFactory()
    build_flow.save()
    flowtask1 = FlowTaskFactory(build_flow=build_flow)
    flowtask1.save()
    flowtask2 = FlowTaskFactory(build_flow=build_flow)
    flowtask2.save()
    path = PurePath(__file__).parent.parent.parent

    output_1 = path / "testresults/tests/robot_1.xml"

    output_2 = path / "testresults" / "tests" / "robot_screenshots.xml"
    ss_1_path = Path(path / "selenium-screenshot-1.png")
    ss_2_path = Path(path / "selenium-screenshot-2.png")

    result = mock.Mock(return_values={"robot_outputdir": str(output_1)})
    step_spec = mock.Mock(path="test_flow_name.Robot", step_num="1.1")

    metaci_callbacks = MetaCIFlowCallback(build_flow.id)
    metaci_callbacks.post_task(step_spec, result)

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
            metaci_callbacks.post_task(step, result)

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
