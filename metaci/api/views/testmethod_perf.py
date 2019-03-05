from django.shortcuts import render
from django.db.models import F, Avg, Count
from django.db import models
from django.forms import SelectDateWidget

import django_filters.rest_framework

from rest_framework import generics, filters

from metaci.testresults.models import TestResult
from metaci.build.models import BuildFlow
from metaci.build.filters import BuildFilter
from metaci.api.serializers.testmethod_perf import TestMethodPerfSerializer
from metaci.repository.models import Repository
from metaci.plan.models import Plan


class TestMethodPerfFilter(django_filters.rest_framework.FilterSet):
    def __init__(self, *args, **kwargs):
        print("***** INITIALIZXED ***", args, kwargs)
        super(TestMethodPerfFilter, self).__init__(*args, **kwargs)

    method_name = django_filters.rest_framework.CharFilter(field_name="method_name",
        label="Method Name")

    # we implement many of these "by hand" in get_queryset, so we don't want them
    # here too. They should be implemented in the view because they filter the
    # buildflow list, not the output.
    dummy_filter = lambda queryset, name, value:  queryset

    repo_choices = Repository.objects.values_list('name', 'name').order_by('name').distinct()
    repo = django_filters.rest_framework.ChoiceFilter(field_name="repo", label="Repo Name", 
         choices = repo_choices, method = dummy_filter)

    plan_choices = Plan.objects.values_list('name', 'name').order_by('name').distinct()
    plan = django_filters.rest_framework.ChoiceFilter(field_name="plan", label="Plan Name", 
         choices = plan_choices, method = dummy_filter)

    flow_choices = BuildFlow.objects.values_list('flow', 'flow').order_by('flow').distinct()
    flow = django_filters.rest_framework.ChoiceFilter(field_name="flow",
         label="Flow Name", choices = flow_choices,
         method = dummy_filter)

    foobar = django_filters.rest_framework.DateRangeFilter(field_name="xyzzy",
        label="Date range (unimplemented)", method = dummy_filter,
        )

    # foobar2 = django_filters.rest_framework.DateFromToRangeFilter(field_name="xyzzy",
    #     label="Date range (unimplemented)", method = dummy_filter,
    #     widget = SelectDateWidget)


    o = django_filters.rest_framework.OrderingFilter(
        fields=(
            ('method_name', 'method_name'),
            ('avg', 'avg'),
            ('count', 'count'),
        ),
    )



class TestMethodPerfListView(generics.ListAPIView):
    """
    A view for lists of aggregated test metrics
    """

    serializer_class = TestMethodPerfSerializer
    filter_backends = (django_filters.rest_framework.DjangoFilterBackend,)
    filter_class = TestMethodPerfFilter

    # example URLs:
    # http://localhost:8000/api/testmethod_perf/?repo=gem&plan=Release%20Test&method_name=testCreateNegative
    # http://localhost:8000/api/testmethod_perf/?repo=Cumulus&plan=Feature%20Test&o=avg

    def get_queryset(self):
        range_start = "2018-02-04 01:01:24.777558+00"
        range_end = "2019-02-04 17:38:24.777558+00"
        build_flows_limit = 100
        test_results_limit = 100
        metric = self.request.query_params.get("metric") or "duration"
        print("KWARGS", self.kwargs)
        print(self.kwargs.get("repo"))
        print("ARGS", self.args)
        print("GET", self.request.query_params.get("repo"))

        buildflows = (BuildFlow.objects
                .filter(time_end__isnull = False)
                .filter(time_end__gt = range_start)
                .filter(time_end__lt = range_end))
        get = self.request.query_params.get

        param_filters = (("repo", "build__repo__name"), 
                    ("plan", "build__plan__name"), 
                    ("branch", "build__branch__name"),
                    ("flow", "flow"))

        for param, filtername in param_filters:
            if get(param): 
                buildflows = buildflows.filter(**{filtername: get(param)})
                
        buildflows = buildflows[0:build_flows_limit]
        
        print(str(buildflows.query))

        queryset = TestResult.objects.filter(
                build_flow_id__in = buildflows)\
                        .values(method_name = F('method__name'), 
                                repo = F('build_flow__build__repo__name'),
#                                plan = F('build_flow__build__plan__name'),
#                                flow = F('build_flow__flow'),
#                                branch = F('build_flow__build__branch__name'),
                                )\
                                .annotate(count = Count('id'), avg = Avg(metric))
        print(str(queryset.query))
# 
        return queryset


