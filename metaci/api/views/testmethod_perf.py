import copy

from django.db.models import FloatField
from django.db.models.functions import Cast

from django.db.models import F, Avg, Count, Q, Min, Max

import django_filters.rest_framework
from django_filters.widgets import DateRangeWidget
from django_filters.rest_framework import DateRangeFilter

from rest_framework import generics, exceptions, viewsets

from metaci.testresults.models import TestResult
from metaci.build.models import BuildFlow
from metaci.api.serializers.testmethod_perf import TestMethodPerfSerializer
from metaci.repository.models import Repository, Branch
from metaci.plan.models import Plan

from django.db import connection


def set_timeout(timeout):
    """Restrict extremely long Postgres queries.
    Theoretically this should reset on the next request but that
    could use some additional testing"""
    with connection.cursor() as cursor:
        cursor.execute("SET LOCAL statement_timeout=%s", [timeout * 1000])


class TurnFilterSetOffByDefaultBase(django_filters.rest_framework.FilterSet):
    """A bit of a hack to allow two filtersets to work together in generating the
       djago-filter config form but to have only one of them actually filter the
       output queryset. The other filters a queryset of a sub-select."""

    really_filter = False

    def __init__(self, *args, really_filter=really_filter, **kwargs):
        self.really_filter = really_filter
        super().__init__(*args, **kwargs)

        for filtername in self.filters.keys():
            if not really_filter:
                if filtername in self.disable_by_default:
                    self.filters[filtername] = copy.copy(self.filters[filtername])
                    self.filters[filtername].method = self.dummy_filter

    def dummy_filter(self, queryset, name, value):
        return queryset


class BuildFlowFilterSet(TurnFilterSetOffByDefaultBase):
    """
       The tricky bit is that this filter serves three different jobs.

        1. It validates incoming parameters (which is not strictly necessary
          but probably difficult to turn off and perhaps sometimes useful).

        2. It populates the django-filter form.

        3. It drives actual filtering of the build-list sub-query.

        Feature 3 is turned on and off by the really_filter parameter.
        We do NOT want django-filter to try to automatically filter the
        output queryset based on these filters because it is actually the
        sub-query that we need to filter.

        Accordingly, its fields are turned off by default (see disable_by_default) 
        and turned on explicitly ("really_filter") when it is created by get_queryset
       """

    build_fields = {
        "repo": "build__repo__name",
        "plan": "build__plan__name",
        "branch": "build__branch__name",
        "flow": "flow",
    }

    repo_choices = (
        Repository.objects.values_list("name", "name").order_by("name").distinct()
    )
    repo = django_filters.rest_framework.ChoiceFilter(
        field_name="build__repo__name", label="Repo Name", choices=repo_choices
    )

    branch_choices = (
        Branch.objects.values_list("name", "name").order_by("name").distinct()
    )
    branch = django_filters.rest_framework.ChoiceFilter(
        field_name="build__branch__name", label="Branch Name", choices=branch_choices
    )

    plan_choices = Plan.objects.values_list("name", "name").order_by("name").distinct()
    plan = django_filters.rest_framework.ChoiceFilter(
        field_name="build__plan__name", label="Plan Name", choices=plan_choices
    )

    flow_choices = (
        BuildFlow.objects.values_list("flow", "flow").order_by("flow").distinct()
    )
    flow = django_filters.rest_framework.ChoiceFilter(
        field_name="flow", label="Flow Name", choices=flow_choices
    )

    recentdate = DateRangeFilter(label="Recent Date", field_name="time_end")

    daterange = django_filters.rest_framework.DateFromToRangeFilter(
        field_name="time_end",
        label="Date range",
        widget=DateRangeWidget(attrs={"type": "date"}),
    )

    # This is not really a filter. It's actually just a query input but putting it
    # here lets me get it in the form.
    build_flows_limit = django_filters.rest_framework.NumberFilter(
        method="dummy_filter", label="Build Flows Limit (default: 100)"
    )

    disable_by_default = dir()  # disable all of these fields by default.


class TestMethodPerfFilter(BuildFlowFilterSet, django_filters.rest_framework.FilterSet):
    """This filterset works on the output queries"""

    method_name = django_filters.rest_framework.CharFilter(
        field_name="method_name", label="Method Name"
    )

    def dummy(queryset, name, value):
        return queryset

    group_by_choices = tuple(
        (name, name) for name in BuildFlowFilterSet.build_fields.keys()
    )

    group_by = django_filters.rest_framework.MultipleChoiceFilter(
        label="Split On (multi-select okay)", choices=group_by_choices, method=dummy
    )

    metrics = {
        "average_duration": Avg("duration"),
        "slowest_runs": Min("duration"),  # fixme: use p05
        "fastest_runs": Max("duration"),  # fixme: use p95
        "average_cpu_usage": Avg("test_cpu_time_used"),
        "low_cpu_usage": Min("test_cpu_time_used"),
        "high_cpu_usage": Max("test_cpu_time_used"),
        "count": Count("id"),
        "failures": Count("id", filter=Q(outcome="Fail")),
        "assertion_failures": Count(
            "id", filter=Q(message__startswith="System.AssertException")
        ),
        "DML_failures": Count(
            "id", filter=Q(message__startswith="System.DmlException")
        ),
        "Other_failures": Count(
            "id",
            filter=~Q(message__startswith="System.DmlException")
            & ~Q(message__startswith="System.AssertException"),
        ),
        "success_percentage": Cast(Count("id", filter=Q(outcome="Pass")), FloatField())
        / Cast(Count("id"), FloatField()),
    }

    metric_choices = tuple(zip(metrics.keys(), metrics.keys()))
    include_fields = django_filters.rest_framework.MultipleChoiceFilter(
        label="Include (multi-select okay)", choices=metric_choices, method=dummy
    )

    o = django_filters.rest_framework.OrderingFilter(
        fields=(
            metric_choices
            + group_by_choices
            + (
                ("method_name", "method_name"),
                ("count", "count"),
                ("failures", "failures"),
                ("assertion_failures", "assertion_failures"),
                ("DML_failures", "DML_failures"),
                ("Other_failures", "Other_failures"),
                ("success_percentage", "success_percentage"),
            )
        )
    )


BUILD_FLOWS_LIMIT = 100


class TestMethodPerfListView(generics.ListAPIView, viewsets.ViewSet):
    """
    A view for lists of aggregated test metrics.

    Note that the number of build flows covered is limited to **BUILD_FLOWS_LIMIT** for performance reasons. You can
    change this default with the build_flows_limit parameter.
    """

    serializer_class = TestMethodPerfSerializer
    filter_backends = (django_filters.rest_framework.DjangoFilterBackend,)
    filter_class = TestMethodPerfFilter

    # example URLs:
    # http://localhost:8000/api/testmethod_perf/?repo=gem&plan=Release%20Test&method_name=testCreateNegative
    # http://localhost:8000/api/testmethod_perf/?repo=Cumulus&plan=Feature%20Test&o=avg
    # http://localhost:8000/api/testmethod_perf/?method_name=&repo=&plan=&flow=&recentdate=&daterange_after=&daterange_before=&o=-repo

    def _get_buildflows(self):
        """Which buildflows do we need to look at? Limit by time, repo, etc.
           Also limit # for performance reasons"""
        params = self.request.query_params
        build_flows_limit = int(params.get("build_flows_limit") or BUILD_FLOWS_LIMIT)

        buildflows = BuildFlow.objects.filter(tests_total__gte=1)
        buildflows = BuildFlowFilterSet(
            self.request.GET, buildflows, really_filter=True
        ).qs

        return buildflows.order_by("-time_end")[0:build_flows_limit]

    def _get_aggregation_fields(self):
        """What fields should appear in the output?"""
        params = self.request.query_params
        aggregations = {}
        fields_to_include = params.getlist("include_fields")

        if params.get("o"):
            fields_to_include.append(params.get("o"))

        fields = self.filter_class.metrics

        for fieldname in fields_to_include:
            fieldname = fieldname.strip("-")
            aggregations[fieldname] = fields[fieldname]

        print("Aggregating", aggregations)

        return aggregations

    def _get_splitter_fields(self):
        "Which fields to split on (or group by, depending on how you think about it"
        params = self.request.query_params
        output_fields = {}

        build_fields = BuildFlowFilterSet.build_fields
        if params.get("group_by"):
            for param in params.getlist("group_by"):
                output_fields[param] = F("build_flow__" + build_fields[param])

        print("Splitting", output_fields)

        return output_fields

    def _check_params(self):
        "Check things the django-filter does not check automatically"
        params = self.request.query_params
        if params.get("recentdate") and (
            params.get("daterange_after") or params.get("daterange_before")
        ):
            raise exceptions.APIException("Specified both recentdate and daterange")

    def get_queryset(self):
        "The main method that the Django infrastructure invokes."
        set_timeout(20)
        self._check_params()

        buildflows = self._get_buildflows()
        splitter_fields = self._get_splitter_fields()
        aggregations = self._get_aggregation_fields()

        queryset = (
            TestResult.objects.filter(
                build_flow_id__in=buildflows, duration__isnull=False
            )
            .values(method_name=F("method__name"), **splitter_fields)
            .annotate(**aggregations)
        )

        return queryset


# A bit of hackery to make a dynamic docstring, because the docstring
# appears in the UI.
TestMethodPerfListView.__doc__ = TestMethodPerfListView.__doc__.replace(
    "BUILD_FLOWS_LIMIT", str(BUILD_FLOWS_LIMIT)
)
