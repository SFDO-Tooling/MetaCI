import logging

from cumulusci.core.flowrunner import FlowCallback
from django.conf import settings
from django.utils import timezone

from metaci.testresults.robot_importer import (
    export_robot_test_results,
    import_robot_test_results,
)

from .models import FlowTask

logger = logging.getLogger("cumulusci")


class MetaCIFlowCallback(FlowCallback):
    """An implementation of FlowCallback that logs task execution to the database."""

    def __init__(self, buildflow_id):
        self.buildflow_id = buildflow_id

    def pre_task(self, step):
        flowtask = FlowTask.objects.find_task(
            self.buildflow_id, step.path, step.step_num
        )
        flowtask.description = step.task_config.get("description")
        flowtask.time_start = timezone.now()
        flowtask.options = step.task_config["options"]
        flowtask.class_path = step.task_class.__name__
        flowtask.status = "running"

        flowtask.save()

    def post_task(self, step, result):
        flowtask = FlowTask.objects.find_task(
            self.buildflow_id, step.path, step.step_num
        )
        flowtask.time_end = timezone.now()
        flowtask.result = result.result
        flowtask.return_values = result.return_values

        if result.exception:
            flowtask.exception = result.exception.__class__
            flowtask.status = "error"
        else:
            flowtask.status = "complete"
        flowtask.save()
        if "robot_outputdir" in result.return_values:
            test_results = import_robot_test_results(
                flowtask, result.return_values["robot_outputdir"]
            )
            if settings.METACI_RESULT_EXPORT_ENABLED:
                try:
                    export_robot_test_results(flowtask, test_results)
                except Exception as e:
                    logger.info(f"Error exporting test result: {e}")
