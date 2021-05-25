import json

from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse, HttpResponseBadRequest
from django_rq.queues import get_connection, get_queue_by_index
from django_rq.settings import QUEUES_LIST
from rq import Worker
from rq.registry import DeferredJobRegistry, FinishedJobRegistry, StartedJobRegistry


def test(request):
    """
    Doesn't do much except telling the HireFire bot it's installed.
    """
    return HttpResponse("OK")


def info(request, token):
    """
    Return the HireFire json data needed to scale worker dynos
    """
    if not settings.HIREFIRE_TOKEN:
        return HttpResponseBadRequest(
            "Hirefire not configured.  Set the HIREFIRE_TOKEN environment variable on the app to use Hirefire for dyno scaling"
        )
    if token != settings.HIREFIRE_TOKEN:
        raise PermissionDenied("Invalid token")

    current_tasks = 0

    queues = []
    for index, config in enumerate(QUEUES_LIST):

        queue = get_queue_by_index(index)
        connection = queue.connection

        # Only look at the default queue
        if queue.name != "default":
            continue

        queue_data = {
            "name": queue.name,
            "jobs": queue.count,
            "index": index,
            "connection_kwargs": connection.connection_pool.connection_kwargs,
        }

        connection = get_connection(queue.name)
        all_workers = Worker.all(connection=connection)
        queue_workers = [worker for worker in all_workers if queue in worker.queues]
        queue_data["workers"] = len(queue_workers)

        finished_job_registry = FinishedJobRegistry(queue.name, connection)
        started_job_registry = StartedJobRegistry(queue.name, connection)
        deferred_job_registry = DeferredJobRegistry(queue.name, connection)
        queue_data["finished_jobs"] = len(finished_job_registry)
        queue_data["started_jobs"] = len(started_job_registry)
        queue_data["deferred_jobs"] = len(deferred_job_registry)

        current_tasks += queue_data["jobs"]
        current_tasks += queue_data["started_jobs"]

        queues.append(queue_data)

    payload = [{"quantity": current_tasks, "name": "worker"}]

    payload = json.dumps(payload)
    return HttpResponse(payload, content_type="application/json")
