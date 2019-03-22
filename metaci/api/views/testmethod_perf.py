import copy

from django.db.models import FloatField
from django.db.models.functions import Cast

from django.db.models import F, Avg, Count, Q, StdDev

import django_filters.rest_framework
from django_filters.widgets import DateRangeWidget
from django_filters.rest_framework import DateRangeFilter

from postgres_stats.aggregates import Percentile

from rest_framework import generics, exceptions, viewsets, pagination

from metaci.testresults.models import TestResult
from metaci.build.models import BuildFlow
from metaci.api.serializers.simple_dict_serializer import SimpleDictSerializer
from metaci.repository.models import Repository, Branch
from metaci.plan.models import Plan

from django.db import connection


def NearMin(field):
    "DB Statistical function for almost the minimum but not quite."
    return Percentile(field, 0.5, output_field=FloatField())


def NearMax(field):
    "DB Statistical function for almost the maximum but not quite."
    return Percentile(field, 0.95, output_field=FloatField())


def set_timeout(timeout):
    """Restrict extremely long Postgres queries.

    Theoretically this should reset on the next request but that
    could use some additional testing.
    """
    with connection.cursor() as cursor:
        cursor.execute("SET LOCAL statement_timeout=%s", [timeout * 1000])


class TurnFilterSetOffByDefaultBase(django_filters.rest_framework.FilterSet):
    """A bit of a hack class. Use carefully!
    
    This is a bit of a hack to allow two filtersets to work together in
    generating the djago-filter config form but to have only one of them
    actually filter the output queryset. The other filters a queryset of
    a sub-select.
    """

    def __init__(self, *args, really_filter=False, **kwargs):
        super().__init__(*args, **kwargs)

        if not really_filter:
            for filtername in self.filters.keys():
                if filtername in self.disable_by_default:
                    self.filters[filtername] = copy.copy(self.filters[filtername])
                    self.filters[filtername].method = self.dummy_filter

    def dummy_filter(self, queryset, name, value):
        return queryset


class StandardResultsSetPagination(pagination.PageNumberPagination):
    page_size = 50
    page_size_query_param = "page_size"
    max_page_size = 1000


class BuildFlowFilterSet(TurnFilterSetOffByDefaultBase):
    """A "conditional" filterset for generating the BuildFlow sub-select.

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

    disable_by_default = []

    repo_choices = (
        Repository.objects.values_list("name", "name").order_by("name").distinct()
    )
    repo = django_filters.rest_framework.ChoiceFilter(
        field_name="build__repo__name", label="Repo Name", choices=repo_choices
    )
    disable_by_default.append("repo")

    branch_choices = (
        Branch.objects.values_list("name", "name").order_by("name").distinct()
    )
    branch = django_filters.rest_framework.ChoiceFilter(
        field_name="build__branch__name", label="Branch Name", choices=branch_choices
    )
    disable_by_default.append("branch")

    plan_choices = Plan.objects.values_list("name", "name").order_by("name").distinct()
    plan = django_filters.rest_framework.ChoiceFilter(
        field_name="build__plan__name", label="Plan Name", choices=plan_choices
    )
    disable_by_default.append("plan")

    flow_choices = (
        BuildFlow.objects.values_list("flow", "flow").order_by("flow").distinct()
    )
    flow = django_filters.rest_framework.ChoiceFilter(
        field_name="flow", label="Flow Name", choices=flow_choices
    )
    disable_by_default.append("flow")

    recentdate = DateRangeFilter(label="Recent Date", field_name="time_end")
    disable_by_default.append("recentdate")

    daterange = django_filters.rest_framework.DateFromToRangeFilter(
        field_name="time_end",
        label="Date range",
        widget=DateRangeWidget(attrs={"type": "date"}),
    )
    disable_by_default.append("daterange")

    # This is not really a filter. It's actually just a query input but putting it
    # here lets me get it in the form.
    build_flows_limit = django_filters.rest_framework.NumberFilter(
        method="dummy_filter", label="Build Flows Limit (default: 100)"
    )

    fields_and_stuff = locals()

    build_fields = {}

    for name in ("repo", "plan", "branch", "flow"):
        # make a list of db field_names for use in grouping
        build_fields[name] = fields_and_stuff[name].field_name


class TestMethodPerfFilterSet(
    BuildFlowFilterSet, django_filters.rest_framework.FilterSet
):
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
        "duration_average": Avg("duration"),
        "duration_slow": NearMax("duration"),
        "duration_fast": NearMin("duration"),
        "duration_stddev": StdDev("duration"),
        "duration_coefficient_var": StdDev("duration") / Avg("duration"),
        "cpu_usage_average": Avg("test_cpu_time_used"),
        "cpu_usage_low": NearMin("test_cpu_time_used"),
        "cpu_usage_high": NearMax("test_cpu_time_used"),
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

    ordering_fields = (
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
    o = django_filters.rest_framework.OrderingFilter(fields=ordering_fields)
    ordering_param_name = "o"


BUILD_FLOWS_LIMIT = 100


class MetaCIApiException(exceptions.APIException):
    status_code = 400
    default_detail = "Validation Error."
    default_code = 400


class TestMethodPerfListView(generics.ListAPIView, viewsets.ViewSet):
    """A view for lists of aggregated test metrics.

    Note that the number of build flows covered is limited to **BUILD_FLOWS_LIMIT** for performance reasons. You can
    change this default with the build_flows_limit parameter.
    """

    serializer_class = SimpleDictSerializer
    filter_backends = (django_filters.rest_framework.DjangoFilterBackend,)
    filterset_class = TestMethodPerfFilterSet
    pagination_class = StandardResultsSetPagination
    ordering_param_name = filterset_class.ordering_param_name

    # example URLs:
    # http://localhost:8000/api/testmethod_perf/?repo=gem&plan=Release%20Test&method_name=testCreateNegative
    # http://localhost:8000/api/testmethod_perf/?repo=Cumulus&plan=Feature%20Test&o=avg
    # http://localhost:8000/api/testmethod_perf/?method_name=&repo=&plan=&flow=&recentdate=&daterange_after=&daterange_before=&o=-repo

    @property
    def orderby_field(self):
        return self.request.query_params.get(self.ordering_param_name)

    def _get_buildflows(self):
        """Which buildflows do we need to look at? Limit by time, repo, etc.

        Also limits # of returned buildflows for performance reasons
        """
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

        if self.orderby_field:
            fields_to_include.append(self.orderby_field)

        fields = self.filterset_class.metrics

        for fieldname in fields_to_include:
            fieldname = fieldname.strip("-")
            if fields.get(fieldname):
                aggregations[fieldname] = fields[fieldname]

        return aggregations

    def _get_splitter_fields(self):
        """Which fields to split on (or group by, depending on how you think about it"""
        params = self.request.query_params
        output_fields = {}
        build_fields = BuildFlowFilterSet.build_fields
        group_by_fields = params.getlist("group_by")
        order_by_field = self.orderby_field

        if order_by_field and order_by_field in build_fields:
            group_by_fields.append(order_by_field)

        if group_by_fields:
            for param in group_by_fields:
                output_fields[param] = F("build_flow__" + build_fields[param])

        return output_fields

    def _check_params(self):
        """Check things the django-filter does not check automatically"""
        params = self.request.query_params
        if params.get("recentdate") and (
            params.get("daterange_after") or params.get("daterange_before")
        ):
            raise MetaCIApiException(
                detail="Specified both recentdate and daterange", code=400
            )

    def get_queryset(self):
        """The main method that the Django infrastructure invokes."""
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

        if not self.orderby_field:
            queryset = queryset.order_by("method_name")

        return queryset


# A bit of hackery to make a dynamic docstring, because the docstring
# appears in the UI.
TestMethodPerfListView.__doc__ = TestMethodPerfListView.__doc__.replace(
    "BUILD_FLOWS_LIMIT", str(BUILD_FLOWS_LIMIT)
)
