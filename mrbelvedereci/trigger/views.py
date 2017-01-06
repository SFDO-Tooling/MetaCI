from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.shortcuts import get_object_or_404

from mrbelvedereci.build.utils import view_queryset
from mrbelvedereci.trigger.models import Trigger
from mrbelvedereci.trigger.forms import RunTriggerForm


def trigger_list(request, trigger_id):
    return ''

def trigger_detail(request, trigger_id):
    query = {'id': trigger_id}
    if not request.user.is_staff:
        query['public'] = True
    trigger = get_object_or_404(Trigger, **query)

    query = {'trigger': trigger}
    builds = view_queryset(request, query)

    context = {
        'builds': builds,
        'trigger': trigger,
    } 
    return render(request, 'trigger/detail.html', context=context)
    
@login_required
def trigger_run(request, trigger_id):
    trigger = get_object_or_404(Trigger, id = trigger_id)

    if request.method == 'POST':
        form = RunTriggerForm(trigger, request.POST)
        if form.is_valid():
            build = form.create_build()
            return HttpResponseRedirect(build.get_absolute_url())
    else:
        form = RunTriggerForm(trigger)
    context = {
        'trigger': trigger,
        'form': form,
    }
    return render(request, 'trigger/run.html', context=context)
