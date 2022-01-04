from django.conf import settings
from django.contrib.auth.decorators import permission_required
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.utils import timezone
from watson import search as watson

from metaci.build.filters import BuildFilter
from metaci.build.forms import QATestingForm
from metaci.build.models import Build, Rebuild
from metaci.build.utils import view_queryset


def build_list(request):
    query = {}
    repo = request.GET.get("repo")
    if repo:
        query["repo__name"] = repo

    build_filter, builds = view_queryset(
        request, query, request.GET.get("status"), filterset_class=BuildFilter
    )
    context = {"filter": build_filter, "builds": builds}
    return render(request, "build/build_list.html", context=context)


def build_detail_base(request, build_id, rebuild_id):
    build = get_object_or_404(Build, id=build_id)
    rebuild = None

    if not request.user.has_perm("plan.view_builds", build.planrepo):
        raise PermissionDenied("You are not authorized to view this build")

    if not rebuild_id:
        if build.current_rebuild:
            flows = build.current_rebuild.flows
        else:
            flows = build.flows
    else:
        if rebuild_id == "original":
            flows = build.flows.filter(rebuild__isnull=True)
        else:
            rebuild = get_object_or_404(Rebuild, build_id=build.id, id=rebuild_id)
            flows = rebuild.flows

    flows = flows.order_by("time_queue")

    tests = {"total": 0, "pass": 0, "fail": 0, "failed_tests": []}

    for flow in flows.all():
        if flow.tests_total:
            tests["total"] += flow.tests_total
        if flow.tests_pass:
            tests["pass"] += flow.tests_pass
        if flow.tests_fail:
            tests["fail"] += flow.tests_fail
            tests["failed_tests"].extend(
                list(flow.test_results.filter(outcome__in=["Fail", "CompileFail"]))
            )

    obj_perms = {
        "rebuild_builds": request.user.has_perm("plan.rebuild_builds", build.planrepo),
        "org_login": request.user.has_perm("plan.org_login", build.planrepo),
        "qa_build": request.user.has_perm("plan.qa_build", build.planrepo),
    }

    return (
        build,
        {
            "build": build,
            "rebuild": rebuild,
            "original_build": rebuild_id == "original",
            "tab": None,
            "flows": flows,
            "tests": tests,
            "obj_perms": obj_perms,
        },
    )


@transaction.non_atomic_requests
def build_detail(request, build_id, rebuild_id=None):
    build, context = build_detail_base(request, build_id, rebuild_id)
    return render(request, "build/detail.html", context=context)


@transaction.non_atomic_requests
def build_detail_flows(request, build_id, rebuild_id=None):
    build, context = build_detail_base(request, build_id, rebuild_id)
    context["tab"] = "flows"
    return render(request, "build/detail_flows.html", context=context)


@transaction.non_atomic_requests
def build_detail_tests(request, build_id, rebuild_id=None):
    build, context = build_detail_base(request, build_id, rebuild_id)
    context["tab"] = "tests"
    return render(request, "build/detail_tests.html", context=context)


@transaction.non_atomic_requests
def build_detail_rebuilds(request, build_id, rebuild_id=None):
    build, context = build_detail_base(request, build_id, rebuild_id)
    context["tab"] = "rebuilds"
    return render(request, "build/detail_rebuilds.html", context=context)


@transaction.non_atomic_requests
def build_detail_org(request, build_id, rebuild_id=None):
    build, context = build_detail_base(request, build_id, rebuild_id)

    if not request.user.has_perm("plan.org_login", build.planrepo):
        raise PermissionDenied("You are not authorized to view this build org")

    context["can_log_in"] = (
        build.org.scratch or settings.METACI_ALLOW_PERSISTENT_ORG_LOGIN
    )

    context["tab"] = "org"
    rebuild = context["rebuild"]
    if rebuild and rebuild.org_instance:
        context["org_instance"] = rebuild.org_instance
    else:
        context["org_instance"] = build.org_instance
    return render(request, "build/detail_org.html", context=context)


@transaction.non_atomic_requests
def build_detail_qa(request, build_id, rebuild_id=None):
    build, context = build_detail_base(request, build_id, rebuild_id)

    if not request.user.has_perm("plan.qa_builds", build.planrepo):
        raise PermissionDenied("You are not authorized to qa this build")

    context["tab"] = "qa"
    if request.method == "POST":
        form = QATestingForm(build, request.user, request.POST)
        if form.is_valid():
            form.save()
            build = Build.objects.get(id=build.id)
            context["build"] = build
    else:
        form = QATestingForm(build, request.user)
    context["form"] = form
    return render(request, "build/detail_qa.html", context=context)


def build_rebuild(request, build_id):
    build = get_object_or_404(Build, id=build_id)

    if not request.user.has_perm("plan.rebuild_builds", build.planrepo):
        raise PermissionDenied("You are not authorized to rebuild this build")

    rebuild = Rebuild(build=build, user=request.user, status="queued")
    rebuild.save()

    if not build.log:
        build.log = ""

    build.log += (
        f"\n=== Build restarted at {timezone.now()} by {request.user.username} ===\n"
    )
    build.current_rebuild = rebuild
    build.save()

    return HttpResponseRedirect(f"/builds/{build.id}")


@permission_required("build.search_builds")
def build_search(request):
    results = []

    q = request.GET.get("q")
    if q:
        results = watson.search(q)

    context = {"query": q, "search_entry_list": results}

    return render(request, "build/search.html", context=context)
