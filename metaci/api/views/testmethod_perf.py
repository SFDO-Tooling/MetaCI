from django.shortcuts import render
from django.db.models import F, Avg, Count
from django.db import models
from django.forms import SelectDateWidget, DateInput

import django_filters.rest_framework
from django_filters.widgets import DateRangeWidget, SuffixedMultiWidget
from django_filters.rest_framework import DateRangeFilter

from rest_framework import generics, filters

from metaci.testresults.models import TestResult
from metaci.build.models import BuildFlow
from metaci.build.filters import BuildFilter
from metaci.api.serializers.testmethod_perf import TestMethodPerfSerializer
from metaci.repository.models import Repository
from metaci.plan.models import Plan


class LessAwfulDateRangeWidget(DateRangeWidget):
    def __init__(self, attrs = None):
        widgets = (SelectDateWidget, SelectDateWidget)
        super(SuffixedMultiWidget, self).__init__(widgets, attrs)


class TestMethodPerfFilter(django_filters.rest_framework.FilterSet):
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

    recentdate = DateRangeFilter(
        label="Recent Date", method = dummy_filter,
        )

    daterange = django_filters.rest_framework.DateFromToRangeFilter(
         label="Date range", method = dummy_filter,
         widget = DateRangeWidget(attrs={'type': 'date'})
         )

    o = django_filters.rest_framework.OrderingFilter(
        fields=(
            ('method_name', 'method_name'),
            ('avg', 'avg'),
            ('count', 'count'),
            ('repo', 'repo'),

        ),
    )



class TestMethodPerfListView(generics.ListAPIView):
    """
    A view for lists of aggregated test metrics.

    Note that the number of builds covered is capped at 300 for performance reasons.
    """

    serializer_class = TestMethodPerfSerializer
    filter_backends = (django_filters.rest_framework.DjangoFilterBackend,)
    filter_class = TestMethodPerfFilter

    # example URLs:
    # http://localhost:8000/api/testmethod_perf/?repo=gem&plan=Release%20Test&method_name=testCreateNegative
    # http://localhost:8000/api/testmethod_perf/?repo=Cumulus&plan=Feature%20Test&o=avg
    # http://localhost:8000/api/testmethod_perf/?method_name=&repo=&plan=&flow=&recentdate=&daterange_after=&daterange_before=&o=-repo

    def get_queryset(self):
        build_flows_limit = 100
        metric = self.request.query_params.get("metric") or "duration"
        # print("KWARGS", self.kwargs)
        # print(self.kwargs.get("repo"))
        # print("ARGS", self.args)
        # print("GET", self.request.query_params)

        buildflows = BuildFlow.objects.filter(tests_total__isnull = False)
        get = self.request.query_params.get

        param_filters = (("repo", "build__repo__name"), 
                    ("plan", "build__plan__name"), 
                    ("branch", "build__branch__name"),
                    ("flow", "flow"))

        output_fields = {"repo": F("build_flow__build__repo__name")}

        for param, filtername in param_filters:
            if get(param): 
                buildflows = buildflows.filter(**{filtername: get(param)})
                output_fields[param] = F("build_flow__" + filtername)

        if get("recentdate"):
            buildflows = DateRangeFilter.filters[get("recentdate")](buildflows, "time_end")
        elif get("daterange_after") and get("daterange_before"):
            buildflows = buildflows \
                 .filter(time_end__isnull = False) \
                 .filter(time_end__gte =  get("daterange_after")) \
                 .filter(time_end__lt = get("daterange_before"))

        buildflows = buildflows.order_by("-time_end")[0:build_flows_limit]

        queryset = TestResult.objects.filter(
                build_flow_id__in = buildflows,
                duration__isnull = False)\
                        .values(method_name = F('method__name'), 
                                **output_fields
                                ).annotate(count = Count('id'), avg = Avg(metric))
 
        return queryset

