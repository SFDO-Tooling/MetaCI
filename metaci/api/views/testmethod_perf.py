from django.shortcuts import render
from django.db.models import F, Avg, Count

import django_filters.rest_framework

from rest_framework import generics, filters

from metaci.testresults.models import TestResult
from metaci.build.models import BuildFlow
from metaci.build.filters import BuildFilter
from metaci.api.serializers.testmethod_perf import TestMethodPerfSerializer
from metaci.repository.models import Repository
from metaci.plan.models import Plan

class TestMethodPerfFilter(django_filters.rest_framework.FilterSet):
    method_name = django_filters.rest_framework.CharFilter(field_name="method_name",
        label="Method Name")
    #
    # Doesn't work because it seems to be calling __str__ for some reason
    # 
    # repo = django_filters.rest_framework.ModelChoiceFilter(field_name="repo",
    #     label="Repo Name", queryset = Repository.objects.all(),
    #     to_field_name="name")

    repo = django_filters.rest_framework.ChoiceFilter(field_name="repo",
        label="Repo Name", choices = [(r.name, r.name) for r in Repository.objects.all()],
        required = True)

    plan = django_filters.rest_framework.ChoiceFilter(field_name="plan",
        label="Plan Name", choices = set([(p.name, p.name) for p in Plan.objects.all()]))

    flow = django_filters.rest_framework.ChoiceFilter(field_name="flow",
        label="Flow Name", choices = set([(f.flow, f.flow) for f in BuildFlow.objects.all()]))

    dummy_filter = lambda queryset, name, value:  queryset

    foobar = django_filters.rest_framework.CharFilter(field_name="xyzzy",
        label="Date range (unimplemented)", method = dummy_filter)

    o = django_filters.rest_framework.OrderingFilter(
        # tuple-mapping retains order
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
                .filter(time_end__lt = range_end))[0:build_flows_limit]
        print(str(buildflows.query))

        queryset = TestResult.objects.filter(
                build_flow_id__in = buildflows)\
                        .values(method_name = F('method__name'), 
                                repo = F('build_flow__build__repo__name'),
                                plan = F('build_flow__build__plan__name'),
                                flow = F('build_flow__flow'),
#                                branch = F('build_flow__build__branch__name'),
                                )\
                                .annotate(count = Count('id'), avg = Avg(metric))
        print(str(queryset.query))
# 
        return queryset


