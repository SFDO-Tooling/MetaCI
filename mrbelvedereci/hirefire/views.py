import json

from django.conf import settings
from django.http import HttpResponse
from django.http import HttpResponseForbidden

from celery import _state

def test(request):
    """
    Doesn't do much except telling the HireFire bot it's installed.
    """
    return HttpResponse('OK')

def info(request, token):
    """
    Return the HireFire json data needed to scale worker dynos
    """
    if token != settings.HIREFIRE_TOKEN:
        return HttpResponseForbidden('Invalid token')

    app = _state.default_app
    inspect = app.control.inspect()

    count_active = 0
    active = inspect.active()
    if active:
        for host, tasks in active.items():
            count_active += len(tasks)

    count_scheduled = 0
    scheduled = inspect.scheduled()
    if scheduled:
        for host, tasks in scheduled.items():
            count_scheduled += len(tasks)

    count_reserved = 0
    reserved = inspect.reserved()
    if reserved:
        for host, tasks in reserved.items():
            count_reserved += len(tasks)

    payload = {
        'quantity': count_active + count_scheduled + count_reserved,
        'name': 'worker',
    }

    payload = json.dumps(payload)
    return HttpResponse(payload, content_type='application/json')
