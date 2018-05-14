from cumulusci.core.flows import BaseFlow
from django.utils import timezone

from .models import FlowTask


class MetaCIFlow(BaseFlow):
    """ An implementation of BaseFlow that logs task execution to the database. """

    def __init__(self, *args, **kwargs):
        self.buildflow_id = None
        super(MetaCIFlow, self).__init__(*args, **kwargs)
    
    def _pre_task(self, task):
        flowtask = FlowTask.objects.find_task(self.buildflow_id, task.name, task.stepnum)
        flowtask.description = task.task_config.description
        flowtask.time_start = timezone.now()
        flowtask.options = task.options
        flowtask.class_path = task.__class__.__name__
        flowtask.status = 'running'
        flowtask.save()

    def _post_task(self, task):
        flowtask = FlowTask.objects.find_task(self.buildflow_id, task.name, task.stepnum)
        flowtask.time_end = timezone.now()
        flowtask.result = task.result
        flowtask.return_values = task.return_values
        flowtask.status = 'complete'
        flowtask.save()

    def _post_task_exception(self, task, e):
        flowtask = FlowTask.objects.find_task(self.buildflow_id, task.name, task.stepnum)
        flowtask.time_end = timezone.now()
        flowtask.result = task.result
        flowtask.return_values = task.return_values
        flowtask.exception = e.__class__
        flowtask.status = 'error'
        flowtask.save()