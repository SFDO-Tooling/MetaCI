import html
import os
import re
from tempfile import mkstemp

from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.views.decorators.clickjacking import xframe_options_exempt
from robot import rebot

from metaci.build.models import Build, BuildFlow
from metaci.build.utils import paginate
from metaci.testresults.filters import BuildFlowFilter
from metaci.testresults.importer import STATS_MAP
from metaci.testresults.models import TestMethod, TestResult, TestResultAsset
from metaci.testresults.utils import find_buildflow

ASSET_URL_RE = re.compile(r'"(buildflow)?asset://(\d+)"')


def build_flow_tests(request, build_id, flow):
    build_flow = find_buildflow(request, build_id, flow)
    data = {"build_flow": build_flow}

    last_class = None
    results_by_class = []
    current_class_results = []

    results_query = build_flow.test_results.select_related(
        "method", "method__testclass"
    )

    # Handle configurable display columns
    columns = request.GET.get("columns", "worst_limit,worst_limit_percent")
    columns = columns.split(",")

    data["columns"] = columns

    # Handle sorting and queryset filtering via GET parameter 'sort'
    sort = request.GET.get("sort", None)
    custom_sort = False
    if sort is None:
        sort = "method__testclass__name,method__name"
    else:
        custom_sort = True
    sort = sort.split(",")

    results_query = results_query.order_by(*sort)

    if custom_sort:
        for sort_field in sort:
            # Handle stripping '-' from start of sort field to handle DESC sorts
            actual_field = sort_field
            if sort_field.startswith("-"):
                actual_field = sort_field[1:]

            # Ensure that the sort field is not null
            results_query = results_query.filter(**{"%s__isnull" % actual_field: False})

    # Group results by Apex Class for display in template
    for result in results_query:

        # If we're entering a new class, add the last class's results to the results_by_class list
        if result.method.testclass != last_class:
            if current_class_results:
                results_by_class.append(
                    {"class": last_class, "results": current_class_results}
                )
                current_class_results = []

        result_data = {"result": result, "columns": []}
        for column in columns:
            column_data = {
                "heading": column,
                "value": getattr(result, column),
                "status": "active",
            }
            set_percent_data(result, column, column_data)

            result_data["columns"].append(column_data)

        current_class_results.append(result_data)
        last_class = result.method.testclass

    # Add the last class's results to the results_by_class list
    if current_class_results:
        results_by_class.append({"class": last_class, "results": current_class_results})

    data["results_by_class"] = results_by_class
    data["sort"] = sort
    data["custom_sort"] = custom_sort
    data["columns"] = columns

    data["assets"] = build_flow.assets.all()

    return render(request, "testresults/build_flow_tests.html", data)


def set_percent_data(result, column, column_data):
    percent = None
    if column.find("percent") != -1:
        percent = column_data["value"]
    elif column.find("used") != -1:
        percent = getattr(result, column.replace("_used", "_percent"))

    if percent is not None:
        if percent < 50:
            column_data["status"] = "success"
        elif percent < 70:
            column_data["status"] = "info"
        elif percent < 80:
            column_data["status"] = "warning"
        else:
            column_data["status"] = "danger"


def test_result_detail(request, result_id):
    build_qs = Build.objects.for_user(request.user)
    result = get_object_or_404(TestResult, id=result_id, build_flow__build__in=build_qs)
    data = {"result": result}
    if result.method.testclass.test_type == "Apex":
        stats = list(STATS_MAP.keys())
        stats.sort()
        test_stats = []
        test_stats.append(
            {
                "limit": "Duration",
                "used": result.duration,
                "allowed": "N/A",
                "percent": "N/A",
            }
        )
        for stat in stats:
            used = getattr(result, f"{stat}_used", None)
            if not used:
                continue
            test_stats.append(
                {
                    "limit": STATS_MAP[stat],
                    "used": used,
                    "allowed": getattr(result, f"{stat}_allowed", None),
                    "percent": getattr(result, f"{stat}_percent", None),
                }
            )
        data["test_stats"] = test_stats

    return render(request, "testresults/test_result_detail.html", data)


def make_asset_resolver(result):
    def resolve_asset_url(m):
        url = ""
        asset_type = m.group(1)
        if asset_type == "buildflow":
            queryset = result.build_flow.assets
        elif asset_type is None:
            queryset = result.assets
        asset_id = int(m.group(2))
        try:
            asset = queryset.get(id=asset_id)
        except ObjectDoesNotExist:
            pass
        else:
            if asset_type == "buildflow":
                url = reverse(
                    "build_flow_download_asset",
                    kwargs={
                        "build_id": result.build_flow.build.pk,
                        "flow": result.build_flow.flow,
                        "build_flow_asset_id": asset.pk,
                    },
                )
            else:
                url = reverse(
                    "testresult_download_asset",
                    kwargs={
                        "result_id": asset.result.pk,
                        "testresult_asset_id": asset.pk,
                    },
                )
        return '"{}"'.format(html.escape(url))

    return resolve_asset_url


@xframe_options_exempt
def test_result_robot(request, result_id):
    build_qs = Build.objects.for_user(request.user)
    result = get_object_or_404(TestResult, id=result_id, build_flow__build__in=build_qs)

    if result.robot_xml:
        # resolve linked assets into temporary S3 URLs
        robot_xml = ASSET_URL_RE.sub(make_asset_resolver(result), result.robot_xml)

        source = mkstemp()[1]
        log = mkstemp(".html")[1]
        rebot_options = {"log": log, "output": None, "report": None}
        if result.task:
            # Copy subset of robot task options that affect the log
            options_to_copy = (
                "name",
                "doc",
                "metadata",
                "settag",
                "critical",
                "noncritical",
                "logtitle",
                "suitestatlevel",
                "tagstatinclude",
                "tagstatexclude",
                "tagstatcombine",
                "tagdoc",
                "tagstatlink",
                "removekeywords",
                "flattenkeywords",
            )
            options = result.task.options.get("options", {})
            rebot_options.update(
                {k: options[k] for k in options_to_copy if k in options}
            )

        with open(source, "w") as f:
            f.write(robot_xml)
        rebot(source, **rebot_options)
        with open(log, "r") as f:
            log_html = f.read()
        log_html = patch_html(log_html)
        os.remove(source)
        os.remove(log)
        return HttpResponse(log_html)
    else:
        return HttpResponse(f"No robot_xml available in test result: {result}")


def patch_html(html):
    """Patch anchor elements to specify the target attribute

    The links created by the tagstatlink option will fail to
    open when viewed within a frame. Even if that weren't the
    case, I don't think we want them to open up in the frame
    inside a metaci test result page.

    This adds `target=_top` to the generated links.
    """
    # Yeah, I know patching HTML is fraught with peril. The robot
    # code to generate the logs is pretty stable, so I think
    # this is a reasonably safe way to do it. It results in a
    # much better experience for our users.
    html = html.replace(
        r'<span>[<a href="{{html $value.url}}" title="{{html $value.url}}">',
        r'<span>[<a href="{{html $value.url}}" title="{{html $value.url}}" target="_top">',
    )
    return html


def test_method_peek(request, method_id):
    build_qs = Build.objects.for_user(request.user)
    method = get_object_or_404(TestMethod, id=method_id)
    latest_fails = (
        method.test_results.filter(outcome="Fail", build_flow__build__in=build_qs)
        .order_by("-build_flow__time_end")
        .select_related(
            "build_flow",
            "build_flow__build",
            "build_flow__build__repo",
            "build_flow__build__plan",
            "build_flow__build__branch",
            "build_flow__build__branch__repo",
        )
    )
    latest_fails = paginate(latest_fails, request)

    data = {"method": method, "latest_fails": latest_fails}

    return render(request, "testresults/test_method_peek.html", data)


@login_required
def test_method_trend(request, method_id):
    build_qs = Build.objects.for_user(request.user)
    method = get_object_or_404(TestMethod, id=method_id)

    latest_results = method.test_results.filter(
        build_flow__build__in=build_qs
    ).order_by("-build_flow__time_end")
    latest_results = paginate(latest_results, request)

    results_by_plan = {}
    i = 0
    for result in latest_results:
        plan_name = (
            result.build_flow.build.plan.name,
            result.build_flow.build.branch.name,
        )
        if plan_name not in results_by_plan:
            # Create the list padded with None for prior columns
            results_by_plan[plan_name] = [None] * i
        results_by_plan[plan_name].append(result)
        i += 1

        # Pad the other field's lists with None values for this column
        for key in results_by_plan.keys():
            if key == plan_name:
                continue
            else:
                results_by_plan[key].append(None)

    results = []
    plan_keys = list(results_by_plan.keys())
    plan_keys.sort()
    for key in plan_keys:
        plan_results = []
        for result in results_by_plan[key]:
            plan_results.append(result)
        results.append((key[0], key[1], plan_results))

    headers = ["Plan", "Branch/Tag"]
    headers += [""] * i

    data = {
        "method": method,
        "headers": headers,
        "results": results,
        "all_results": latest_results,
    }

    return render(request, "testresults/test_method_trend.html", data)


def build_flow_compare(
    request,
):
    """compare two buildflows for their limits usage"""
    execution1_id = request.GET.get("buildflow1", None)
    execution2_id = request.GET.get("buildflow2", None)
    execution1 = get_object_or_404(BuildFlow, id=execution1_id)
    execution2 = get_object_or_404(BuildFlow, id=execution2_id)

    diff = TestResult.objects.compare_results([execution1, execution2])

    context = {"execution1": execution1, "execution2": execution2, "diff": diff}
    return render(request, "testresults/build_flow_compare.html", context)


def build_flow_compare_to(request, build_id, flow):
    """allows the user to select a build_flow to compare against the one they are on."""
    build_flow = find_buildflow(request, build_id, flow)
    # get a list of build_flows that could be compared to
    possible_comparisons = (
        BuildFlow.objects.filter(
            build__repo__exact=build_flow.build.repo,
            status__in=["success", "fail", "error"],
        )
        .exclude(pk=build_flow.id)
        .order_by("build")
    )
    # use a BuildFlowFilter to dynamically filter the queryset (and generate a form to display them)
    comparison_filter = BuildFlowFilter(request.GET, queryset=possible_comparisons)
    # LIMIT 10
    records = comparison_filter.qs[:10]

    data = {"build_flow": build_flow, "filter": comparison_filter, "records": records}
    return render(request, "testresults/build_flow_compare_to.html", data)


def build_flow_download_asset(request, build_id, flow, build_flow_asset_id):
    build_flow = find_buildflow(request, build_id, flow)
    asset = build_flow.assets.get(id=build_flow_asset_id)
    content_type = "text/xml" if asset.category == "robot-output" else "image/png"
    return _serve_file_response(asset.asset, content_type)


def testresult_download_asset(request, result_id, testresult_asset_id):
    # confirm user has permission for this build
    build_qs = Build.objects.for_user(request.user)
    get_object_or_404(TestResult, id=result_id, build_flow__build__in=build_qs)

    asset = get_object_or_404(
        TestResultAsset, id=testresult_asset_id, result__id=result_id
    )
    return _serve_file_response(asset.asset, "image/png")


def _serve_file_response(file, content_type):
    try:
        response = HttpResponse(file, content_type=content_type)
        response["Content-Disposition"] = (
            "attachment; filename=%s" % file.name.split("/")[-1]
        )
        return response
    except FileNotFoundError:
        raise Http404("File not found.")
