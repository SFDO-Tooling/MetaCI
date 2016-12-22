from django.shortcuts import get_object_or_404
from django.shortcuts import render

from mrbelvedereci.build.models import BuildFlow

def build_flow_tests(request, build_id, flow):
    build_flow = get_object_or_404(BuildFlow, build_id=build_id, flow=flow)
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
