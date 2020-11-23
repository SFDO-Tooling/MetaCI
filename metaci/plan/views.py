from django.core.exceptions import PermissionDenied
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, render

from metaci.build.utils import view_queryset
from metaci.plan.forms import RunPlanForm
from metaci.plan.models import Plan, PlanRepository
from metaci.repository.models import Repository


def can_run_plan(user, plan_id):
    """Checks that the user is logged in and has needed permission"""
    can_run = False
    if (
        Plan.objects.for_user(user, "plan.run_plan").filter(id=plan_id).count()
        and user.is_authenticated
    ):
        can_run = True
    return can_run


def plan_list(request):
    plans = Plan.objects.for_user(request.user)
    context = {"plans": plans}
    return render(request, "plan/list.html", context=context)


def plan_detail(request, plan_id):
    plan = Plan.objects.get_for_user_or_404(request.user, {"id": plan_id})

    query = {"plan": plan}
    builds = view_queryset(request, query)
    can_run = can_run_plan(request.user, plan_id)

    context = {"builds": builds, "plan": plan, "can_run_plan": can_run}
    return render(request, "plan/detail.html", context=context)


def plan_detail_repo(request, plan_id, repo_owner, repo_name):
    planrepo = PlanRepository.objects.get_for_user_or_404(
        request.user,
        {"repo__owner": repo_owner, "repo__name": repo_name, "plan__id": plan_id},
    )
    query = {"planrepo": planrepo}
    builds = view_queryset(request, query)
    can_run = can_run_plan(request.user, plan_id)

    context = {
        "builds": builds,
        "plan": planrepo.plan,
        "planrepo": planrepo,
        "repo": planrepo.repo,
        "can_run_plan": can_run,
    }
    return render(request, "plan/plan_repo_detail.html", context=context)


def plan_run(request, plan_id):
    plan = get_object_or_404(Plan, id=plan_id)

    if not can_run_plan(request.user, plan_id):
        raise PermissionDenied("You are not authorized to run this plan")

    context = {"plan": plan, "planrepos": plan.planrepository_set.should_run().all()}
    return render(request, "plan/run_select_repo.html", context=context)


def plan_run_repo(request, plan_id, repo_owner, repo_name):
    plan = get_object_or_404(Plan, id=plan_id)
    repo = get_object_or_404(Repository, owner=repo_owner, name=repo_name)
    # this is a little hackish, but it will cause a 404 if the planrepo or the plan are inactive, preventing runplanform from ever occuring.
    planrepo = get_object_or_404(
        PlanRepository, plan_id=plan.id, repo_id=repo.id, active=True, plan__active=True
    )

    if not can_run_plan(request.user, plan_id):
        raise PermissionDenied("You are not authorized to run this plan")

    if request.method == "POST":
        form = RunPlanForm(planrepo, request.user, request.POST)
        if form.is_valid():
            build = form.create_build()
            return HttpResponseRedirect(build.get_absolute_url())
    else:
        form = RunPlanForm(planrepo, request.user, request.GET)
    context = {"form": form, "plan": plan, "repo": repo}
    return render(request, "plan/run.html", context=context)
