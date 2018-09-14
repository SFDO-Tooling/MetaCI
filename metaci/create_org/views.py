from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render

from metaci.plan.models import (
    Plan,
    PlanRepository,
)

@staff_member_required
def create_org(request):
    return render(request, 'create_org/create_org.html')

@staff_member_required
def scratch_org(request):
    plans = Plan.objects.filter(public=False, active=True, type='org').prefetch_related('repos')
    plan_repos = PlanRepository.objects.filter(plan__in=plans, active=True).order_by('repo__name','plan__name')
    
    context = {
        'plans': plans,
        'plan_repos': plan_repos,
    }
    return render(request, 'create_org/scratch_org.html', context=context)

@staff_member_required
def qa_org(request):
    plans = Plan.objects.filter(active=True, type='qa').prefetch_related('repos')
    plan_repos = PlanRepository.objects.filter(plan__in=plans, active=True).order_by('repo__name','plan__name')
    
    context = {
        'plans': plans,
        'plan_repos': plan_repos,
    }
    return render(request, 'create_org/qa_org.html', context=context)
