from cumulusci.core.flowrunner import FlowCallback
from django.utils import timezone

from .models import FlowTask


class MetaCIFlowCallback(FlowCallback):
    """ An implementation of FlowCallback that logs task execution to the database. """

    def __init__(self, buildflow_id):
        self.buildflow_id = buildflow_id
    
    def pre_task(self, task):
        flowtask = FlowTask.objects.find_task(self.buildflow_id, task.name, task.stepnum)
        flowtask.description = task.task_config.description
        flowtask.time_start = timezone.now()
        flowtask.options = task.options
        flowtask.class_path = task.__class__.__name__
        flowtask.status = 'running'
        flowtask.save()

    def post_task(self, task, result):
        flowtask = FlowTask.objects.find_task(self.buildflow_id, task.name, task.stepnum)
        flowtask.time_end = timezone.now()
        flowtask.result = task.result
        flowtask.return_values = task.return_values
        if result.exception:
            flowtask.exception = result.exception.__class__
            flowtask.status = 'error'
        else:
            flowtask.status = 'complete'
        flowtask.save()
