from cumulusci.core.flowrunner import FlowCallback
from django.utils import timezone

from .models import FlowTask


class MetaCIFlowCallback(FlowCallback):
    """ An implementation of FlowCallback that logs task execution to the database. """

    def __init__(self, buildflow_id):
        self.buildflow_id = buildflow_id
    
    def pre_task(self, step):
        flowtask = FlowTask.objects.find_task(self.buildflow_id, step.task_name, step.stepnum)
        flowtask.description = step.task_config.get('description')
        flowtask.time_start = timezone.now()
        flowtask.options = step.task_config['options']
        flowtask.class_path = step.task_class.__name__
        flowtask.status = 'running'
        flowtask.save()

    def post_task(self, step, result):
        flowtask = FlowTask.objects.find_task(self.buildflow_id, step.task_name, step.stepnum)
        flowtask.time_end = timezone.now()
        flowtask.result = result.result
        flowtask.return_values = result.return_values
        if result.exception:
            flowtask.exception = result.exception.__class__
            flowtask.status = 'error'
        else:
            flowtask.status = 'complete'
        flowtask.save()
