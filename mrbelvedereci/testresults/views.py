from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.shortcuts import get_object_or_404
from django.shortcuts import render
from django.shortcuts import redirect

from mrbelvedereci.build.models import Build
from mrbelvedereci.build.models import BuildFlow
from mrbelvedereci.build.utils import paginate
from mrbelvedereci.testresults.models import TestMethod
from mrbelvedereci.testresults.models import TestResult

def build_flow_tests(request, build_id, flow):
    build = get_object_or_404(Build, id=build_id)

    if not build.plan.public and not request.user.is_staff:
        raise Http404()
    query = {'build_id': build_id, 'flow': flow}
    if build.current_rebuild:
        query['rebuild_id'] = build.current_rebuild

    build_flow = get_object_or_404(BuildFlow, **query)
    data = {'build_flow': build_flow}

    last_class = None
    results_by_class = []
    current_class_results = []

    results_query = build_flow.test_results.all()

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

@login_required
def test_method_trend(request, method_id):
    if not request.user.is_staff:
        return redirect('/login/?next=%s' % request.path)

    method = get_object_or_404(TestMethod, id=method_id)
    
    latest_results = method.test_results.order_by('-build_flow__time_end')

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
    # TODO: wrap this in a helper. or somethign?
    # get the build and build_flow specified in the url
    build = get_object_or_404(Build, id=build_id)

    if not build.plan.public and not request.user.is_staff:
        raise Http404()
    query = {'build_id': build_id, 'flow': flow}
    if build.current_rebuild:
        query['rebuild_id'] = build.current_rebuild

    build_flow = get_object_or_404(BuildFlow, **query)

    # get a list of build_flows that could be compared to
    possible_comparisons = BuildFlow.objects.filter(build__repo__exact=1).order_by('-time_end')
    
    data = {'build_flow': build_flow, 'possible_comparisons': possible_comparisons}
    return render(request, 'testresults/build_flow_compare_to.html', data)
