from cumulusci.core.flowrunner import FlowCallback
from cumulusci.tasks.robotframework.robotframework import Robot
from django.utils import timezone

from metaci.testresults.robot_importer import import_robot_test_results

from .models import FlowTask


class MetaCIFlowCallback(FlowCallback):
    """ An implementation of FlowCallback that logs task execution to the database. """

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

        # Parse and
        if str(step.task_class) == Robot:
            import_robot_test_results(flowtask, "output.xml")

        if result.exception:
            flowtask.exception = result.exception.__class__
            flowtask.status = "error"
        else:
            flowtask.status = "complete"

        flowtask.save()
