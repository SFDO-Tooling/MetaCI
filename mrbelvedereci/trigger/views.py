from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.shortcuts import get_object_or_404
from mrbelvedereci.trigger.models import Trigger
from mrbelvedereci.trigger.forms import RunTriggerForm

def trigger_list(request, trigger_id):
    return ''

def trigger_detail(request, trigger_id):
    trigger = get_object_or_404(Trigger, id = trigger_id)
    context = {
        'trigger': trigger,
    } 
    return render(request, 'trigger/detail.html', context=context)
    

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
