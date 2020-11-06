from django.contrib.auth import login
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.shortcuts import render
from django.contrib.auth.decorators import login_required

from metaci.plan.models import Plan, PlanRepository

@login_required
def create_org(request):
    planrepos = PlanRepository.objects.for_user(request.user, "plan.run_plan")
    planrepos.filter(plan__role__in=["scratch", "qa"])
    if not planrepos.count():
        raise PermissionDenied("You are not authorized to create orgs")
    return render(request, "create_org/create_org.html")


def scratch_org(request):
    planrepos = PlanRepository.objects.for_user(request.user, "plan.run_plan")
    planrepos = (
        planrepos.should_run()
        .filter(plan__role="scratch")
        .order_by("repo__name", "plan__name")
    )
    if not planrepos.count():
        raise PermissionDenied("You are not authorized to create orgs")

    context = {"planrepos": planrepos}
    return render(request, "create_org/scratch_org.html", context=context)


def qa_org(request):
    planrepos = PlanRepository.objects.for_user(request.user, "plan.run_plan")
    planrepos = (
        planrepos.should_run()
        .filter(plan__role="qa")
        .order_by("repo__name", "plan__name")
    )
    if not planrepos.count():
        raise PermissionDenied("You are not authorized to create orgs")

    context = {"planrepos": planrepos}
    return render(request, "create_org/qa_org.html", context=context)
