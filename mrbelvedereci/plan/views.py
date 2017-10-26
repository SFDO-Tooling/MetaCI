from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.shortcuts import get_object_or_404

from mrbelvedereci.build.utils import view_queryset
from mrbelvedereci.plan.models import Plan
from mrbelvedereci.plan.forms import RunPlanForm
from mrbelvedereci.repository.models import Repository


def plan_list(request):
    if request.user.is_staff:
        plans = Plan.objects.all()
    else:
        plans = Plan.objects.filter(public=True)
    context = {
        'plans': plans,
    }
    return render(request, 'plan/list.html', context=context)

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
    
def plan_detail_repo(request, plan_id, repo_owner, repo_name):
    query = {'id': plan_id}
    if not request.user.is_staff:
        query['public'] = True
    plan = get_object_or_404(Plan, **query)
    repo = get_object_or_404(Repository, owner=repo_owner, name=repo_name)
    query = {'plan': plan, 'repo': repo}
    builds = view_queryset(request, query)

    context = {
        'builds': builds,
        'plan': plan,
    }
    return render(request, 'plan/detail.html', context=context)

@login_required
def plan_run(request, plan_id):
    plan = get_object_or_404(Plan, id=plan_id)
    context = {'plan': plan}
    return render(request, 'plan/run_select_repo.html', context=context)

@login_required
def plan_run_repo(request, plan_id, repo_owner, repo_name):
    plan = get_object_or_404(Plan, id=plan_id)
    repo = get_object_or_404(Repository, owner=repo_owner, name=repo_name)
    if request.method == 'POST':
        form = RunPlanForm(plan, repo, request.user, request.POST)
        if form.is_valid():
            build = form.create_build()
            return HttpResponseRedirect(build.get_absolute_url())
    else:
        form = RunPlanForm(plan, repo, request.user)
    context = {
        'form': form,
        'plan': plan,
        'repo': repo,
    }
    return render(request, 'plan/run.html', context=context)
