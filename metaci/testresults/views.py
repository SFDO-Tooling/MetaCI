import os
from tempfile import mkstemp
from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.shortcuts import render
from django.shortcuts import redirect
from robot import rebot

from metaci.build.models import Build
from metaci.build.models import BuildFlow
from metaci.build.utils import paginate
from metaci.build.utils import view_queryset
from metaci.testresults.importer import STATS_MAP
from metaci.testresults.models import TestMethod
from metaci.testresults.models import TestResult

from metaci.testresults.filters import BuildFlowFilter
from metaci.testresults.utils import find_buildflow

def build_flow_tests(request, build_id, flow):
    build_flow = find_buildflow(request, build_id, flow)
    data = {'build_flow': build_flow}

    last_class = None
    results_by_class = []
    current_class_results = []

    results_query = build_flow.test_results.select_related("method", "method__testclass")

    # Handle configurable display columns
    columns = request.GET.get('columns', 'worst_limit,worst_limit_percent')
    columns = columns.split(',')

    data['columns'] = columns

    # Handle sorting and queryset filtering via GET parameter 'sort'
    sort = request.GET.get('sort', None)
    custom_sort = False
    if sort is None:
        sort = 'method__testclass__name,method__name'
    else:
        custom_sort = True
    sort = sort.split(',')

    results_query = results_query.order_by(*sort)

    if custom_sort:
        for sort_field in sort:
            # Handle stripping '-' from start of sort field to handle DESC sorts
            actual_field = sort_field
            if sort_field.startswith('-'):
                actual_field = sort_field[1:]

            # Ensure that the sort field is not null
            results_query = results_query.filter(**{'%s__isnull' % actual_field: False})

    # Group results by Apex Class for display in template
    for result in results_query:

        # If we're entering a new class, add the last class's results to the results_by_class list
        if result.method.testclass != last_class:
            if current_class_results:
                results_by_class.append({'class': last_class, 'results': current_class_results})
                current_class_results = []

        result_data = {'result': result, 'columns': []}
        for column in columns:
            column_data = {
                'heading': column,
                'value': getattr(result, column),
                'status': 'active',
            }
            percent = None
            if column.find('percent') != -1:
                percent = column_data['value']
            elif column.find('used') != -1:
                percent = getattr(result, column.replace('_used','_percent'))

            if percent is not None:
                if percent < 50:
                    column_data['status'] = 'success'
                elif percent < 70:
                    column_data['status'] = 'info'
                elif percent < 80:
                    column_data['status'] = 'warning'
                else:
                    column_data['status'] = 'danger'
            result_data['columns'].append(column_data)
        current_class_results.append(result_data)
        last_class = result.method.testclass

    # Add the last class's results to the results_by_class list
    if current_class_results:
       results_by_class.append({'class': last_class, 'results': current_class_results})

    data['results_by_class'] = results_by_class
    data['sort'] = sort
    data['custom_sort'] = custom_sort
    data['columns'] = columns

    return render(request, 'testresults/build_flow_tests.html', data)

def test_result_detail(request, result_id):
    build_qs = view_queryset(request)
    result = get_object_or_404(
        TestResult,
        id=result_id,
        build_flow__build__in=build_qs,
    )
    data = {'result': result}
    if result.method.testclass.test_type == 'Apex':
        stats = STATS_MAP.keys()
        stats.sort()
        test_stats = []
        test_stats.append({
            'limit': 'Duration',
            'used': result.duration,
            'allowed': 'N/A',
            'percent': 'N/A',
        })
        for stat in stats:
            used = getattr(result, '{}_used'.format(stat), None)
            if not used:
                continue
            test_stats.append({
                'limit': STATS_MAP[stat],
                'used': used,
                'allowed': getattr(result, '{}_allowed'.format(stat), None),
                'percent': getattr(result, '{}_percent'.format(stat), None),
            })
        data['test_stats'] = test_stats
        
    return render(request, 'testresults/test_result_detail.html', data)

def test_result_robot(request, result_id):
    build_qs = view_queryset(request)
    result = get_object_or_404(
        TestResult,
        id=result_id,
        build_flow__build__in=build_qs,
    )

    if result.robot_xml:
        source = mkstemp()[1]
        log = mkstemp('.html')[1]
        with open(source, 'w') as f:
            f.write(result.robot_xml)
        rebot(source, log=log, output=None, report=None)
        with open(log, 'r') as f:
            log_html = f.read()
        os.remove(source)
        os.remove(log)
    return HttpResponse(log_html)

def test_method_peek(request, method_id):
    build_qs = view_queryset(request)
    method = get_object_or_404(TestMethod, id=method_id)
    latest_fails = method.test_results.filter(
        outcome='Fail',
        build_flow__build__in=build_qs,
    ).order_by(
        '-build_flow__time_end'
    ).select_related(
        'build_flow',
        'build_flow__build',
        'build_flow__build__repo',
        'build_flow__build__plan',
        'build_flow__build__branch',
        'build_flow__build__branch__repo'
    )
    latest_fails = paginate(latest_fails, request)


    data = {
        'method': method,
        'latest_fails': latest_fails
    }

    return render(request, 'testresults/test_method_peek.html', data)

@login_required
def test_method_trend(request, method_id):
    build_qs = view_queryset(request)
    method = get_object_or_404(TestMethod, id=method_id)

    latest_results = method.test_results.filter(
        build_flow__build__in=build_qs,
    ).order_by('-build_flow__time_end')
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
            results_by_plan[plan_name] = [None,] * i
        results_by_plan[plan_name].append(result)
        i += 1

        # Pad the other field's lists with None values for this column
        for key in results_by_plan.keys():
            if key == plan_name:
                continue
            else:
                results_by_plan[key].append(None)

    results = []
    plan_keys = results_by_plan.keys()
    plan_keys.sort()
    for key in plan_keys:
        plan_results = []
        for result in results_by_plan[key]:
            plan_results.append(result)
        results.append((key[0], key[1], plan_results))


    headers = ['Plan','Branch/Tag']
    headers += ['',] * i

    data = {
        'method': method,
        'headers': headers,
        'results': results,
        'all_results': latest_results,
    }

    return render(request, 'testresults/test_method_trend.html', data)

def build_flow_compare(request,):
    """ compare two buildflows for their limits usage """
    execution1_id = request.GET.get('buildflow1', None)
    execution2_id = request.GET.get('buildflow2', None)
    execution1 = get_object_or_404(BuildFlow, id=execution1_id)
    execution2 = get_object_or_404(BuildFlow, id=execution2_id)

    diff = TestResult.objects.compare_results([execution1,execution2])

    context = {
        'execution1': execution1,
        'execution2': execution2,
        'diff': diff,
    }
    return render(request, 'testresults/build_flow_compare.html', context)

def build_flow_compare_to(request, build_id, flow):
    """ allows the user to select a build_flow to compare against the one they are on. """
    build_flow = find_buildflow(request, build_id, flow)
    # get a list of build_flows that could be compared to
    possible_comparisons = BuildFlow.objects.filter(
        build__repo__exact=build_flow.build.repo,
        status__in=['success','fail','error'],
    ).exclude(pk=build_flow.id).order_by('build')
    # use a BuildFlowFilter to dynamically filter the queryset (and generate a form to display them)
    comparison_filter = BuildFlowFilter(request.GET, queryset=possible_comparisons)
    # LIMIT 10
    records = comparison_filter.qs[:10]
    
    data = {'build_flow': build_flow, 'filter': comparison_filter, 'records': records}
    return render(request, 'testresults/build_flow_compare_to.html', data)
