from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.shortcuts import get_object_or_404

from mrbelvedereci.build.utils import view_queryset
from mrbelvedereci.plan.models import Plan
from mrbelvedereci.plan.forms import RunPlanForm


def plan_list(request, plan_id):
    return ''

def plan_detail(request, plan_id):
    query = {'id': plan_id}
    if not request.user.is_staff:
        query['public'] = True
    plan = get_object_or_404(Plan, **query)

    query = {'plan': plan}
    builds = view_queryset(request, query)

    context = {
        'builds': builds,
        'plan': plan,
    } 
    return render(request, 'plan/detail.html', context=context)
    
@login_required
def plan_run(request, plan_id):
    plan = get_object_or_404(Plan, id = plan_id)

    if request.method == 'POST':
        form = RunPlanForm(plan, request.POST)
        if form.is_valid():
            build = form.create_build()
            build.user = self.request.user
            return HttpResponseRedirect(build.get_absolute_url())
    else:
        form = RunPlanForm(plan)
    context = {
        'plan': plan,
        'form': form,
    }
    return render(request, 'plan/run.html', context=context)
