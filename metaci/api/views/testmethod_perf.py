import copy
from collections import namedtuple

from django.db.models import FloatField
from django.db.models.functions import Cast, Lower

from django.db.models import F, Avg, Count, Q, StdDev

import django_filters.rest_framework
from django_filters.widgets import DateRangeWidget

from postgres_stats.aggregates import Percentile

from rest_framework import generics, exceptions, viewsets, pagination

from metaci.testresults.models import TestResult
from metaci.build.models import BuildFlow
from metaci.api.serializers.simple_dict_serializer import SimpleDictSerializer
from metaci.repository.models import Repository, Branch
from metaci.plan.models import Plan

from django.db import connection


class DEFAULTS:
    build_flows_limit = 100
    page_size = 50
    max_page_size = 100


FieldType = namedtuple("FieldType", ["label", "aggregation"])


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
    page_size = DEFAULTS.page_size
    page_size_query_param = "page_size"
    max_page_size = DEFAULTS.max_page_size


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

    # Django-filter's DateRangeFilter is kind of ... special
    # disable until we can fix it.
    #
    # recentdate = DateRangeFilter(label="Recent Date", field_name="time_end")
    # disable_by_default.append("recentdate")

    daterange = django_filters.rest_framework.DateFromToRangeFilter(
        field_name="time_end",
        label="Date range",
        widget=DateRangeWidget(attrs={"type": "date"}),
    )
    disable_by_default.append("daterange")

    # This is not really a filter. It's actually just a query input but putting it
    # here lets me get it in the django-filters form.
    build_flows_limit = django_filters.rest_framework.NumberFilter(
        method="dummy_filter",
        label="Build Flows Limit (default: 100)",
        initial=DEFAULTS.build_flows_limit,
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

    success_percentage_gt = django_filters.rest_framework.NumberFilter(
        label="Success percentage above",
        field_name="success_percentage",
        lookup_expr="gt",
    )

    success_percentage_lt = django_filters.rest_framework.NumberFilter(
        label="Success percentage below",
        field_name="success_percentage",
        lookup_expr="lt",
    )

    count_gt = django_filters.rest_framework.NumberFilter(
        label="Count above", field_name="count", lookup_expr="gt"
    )

    count_lt = django_filters.rest_framework.NumberFilter(
        label="Count below", field_name="count", lookup_expr="lt"
    )

    method_name = django_filters.rest_framework.CharFilter(
        field_name="method_name", label="Method Name", lookup_expr="icontains"
    )

    def dummy(queryset, name, value):
        return queryset

    # don't include method_name in this list. Its already passed by default
    metrics = {
        "duration_average": FieldType("Duration: Average", Avg("duration")),
        "duration_slow": FieldType("Duration: Slow", NearMax("duration")),
        "duration_fast": FieldType("Duration: Fast", NearMin("duration")),
        "duration_stddev": FieldType("Duration: Stddev", StdDev("duration")),
        "duration_coefficient_var": FieldType(
            "Duration: VarCoef", StdDev("duration") / Avg("duration")
        ),
        "cpu_usage_average": FieldType("CPU Usage: Average", Avg("test_cpu_time_used")),
        "cpu_usage_low": FieldType("CPU Usage: Low", NearMin("test_cpu_time_used")),
        "cpu_usage_high": FieldType("CPU Usage: High", NearMax("test_cpu_time_used")),
        "count": FieldType("Count", Count("id")),
        "failures": FieldType("Failures", Count("id", filter=Q(outcome="Fail"))),
        "assertion_failures": FieldType(
            "Assertion Failures",
            Count("id", filter=Q(message__startswith="System.AssertException")),
        ),
        "DML_failures": FieldType(
            "DML Failures",
            Count("id", filter=Q(message__startswith="System.DmlException")),
        ),
        "Other_failures": FieldType(
            "Other Failures",
            Count(
                "id",
                filter=~Q(message__startswith="System.DmlException")
                & ~Q(message__startswith="System.AssertException"),
            ),
        ),
        "success_percentage": FieldType(
            "Success Percentage",
            Cast(Count("id", filter=Q(outcome="Pass")), FloatField())
            / Cast(Count("id"), FloatField())
            * 100,
        ),
    }

    metric_choices = tuple((key, field.label) for key, field in metrics.items())
    includable_fields = metric_choices + tuple(
        zip(
            BuildFlowFilterSet.build_fields.keys(),
            BuildFlowFilterSet.build_fields.keys(),
        )
    )
    include_fields = django_filters.rest_framework.MultipleChoiceFilter(
        label="Include (multi-select okay)",
        choices=includable_fields,
        method=dummy,
        initial=["repo", "duration_average"],
    )

    ordering_fields = tuple((name, name) for (name, label) in metric_choices)
    ordering_fields += ("method_name", "method_name")
    o = django_filters.rest_framework.OrderingFilter(fields=ordering_fields)
    ordering_param_name = "o"


class MetaCIApiException(exceptions.APIException):
    status_code = 400
    default_detail = "Validation Error."
    default_code = 400


class TestMethodPerfListView(generics.ListAPIView, viewsets.ViewSet):
    """A view for lists of aggregated test metrics.

    Note that the number of build flows covered is limited to **DEFAULTS.build_flows_limit** for performance reasons. You can
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

    def _get_build_flows(self):
        """Which build_flows do we need to look at? Limit by time, repo, etc.

        Also limits # of returned build_flows for performance reasons
        """
        params = self.request.query_params
        build_flows_limit = int(
            params.get("build_flows_limit") or DEFAULTS.build_flows_limit
        )

        build_flows = BuildFlow.objects.filter(tests_total__gte=1)
        build_flows = BuildFlowFilterSet(
            self.request.GET, build_flows, really_filter=True
        ).qs

        return build_flows.order_by("-time_end")[0:build_flows_limit]

    def _get_aggregation_fields(self):
        """What fields should appear in the output?"""
        params = self.request.query_params
        aggregations = {}

        fields_to_include = params.getlist("include_fields")
        filters = self.filterset_class.get_filters()
        fields = self.filterset_class.metrics

        # every field we want to filter on should be in the annotation list
        for param, value in params.items():
            if value and filters.get(param) and fields.get(param):
                fields_to_include.append(filters[param].field_name)

        # the field we want to order on should be in the annotation list
        if self.orderby_field:
            fields_to_include.append(self.orderby_field.strip("-"))

        # method_name is removed because
        # Django doesn't like it if we add it to the annotation list
        # when it is already a field_name
        if "method_name" in fields_to_include:
            fields_to_include.remove("method_name")

        # no fields? Use defaults
        if fields_to_include == []:
            filters = self.filterset_class.get_filters()
            assert filters
            include_filter = filters["include_fields"]
            assert include_filter
            default_include_fields = include_filter.extra["initial"]
            assert default_include_fields

            fields_to_include.extend(default_include_fields)

        # build a dictionary in the form DRF
        for fieldname in fields_to_include:
            if fields.get(fieldname):
                aggregations[fieldname] = fields[fieldname].aggregation

        return aggregations

    def _get_splitter_fields(self):
        """Which fields to split on (or group by, depending on how you think about it)"""
        params = self.request.query_params
        output_fields = {}
        build_fields = BuildFlowFilterSet.build_fields
        group_by_fields = []
        order_by_field = self.orderby_field

        # if the order_by field is a build field
        # then we need to group by it.
        if order_by_field and order_by_field in build_fields:
            group_by_fields.append(order_by_field)

        # if it is in the include_fields list, lets add
        # it too, with group-by behaviour.
        # TODO: Test this logic
        fields_to_include = params.getlist("include_fields")
        build_fields_in_include_fields = set(fields_to_include).intersection(
            set(build_fields.keys())
        )
        for fieldname in build_fields_in_include_fields:
            group_by_fields.append(fieldname)

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
        set_timeout(5)
        self._check_params()

        build_flows = self._get_build_flows()
        splitter_fields = self._get_splitter_fields()
        aggregations = self._get_aggregation_fields()

        queryset = (
            TestResult.objects.filter(
                build_flow_id__in=build_flows, duration__isnull=False
            )
            .values(method_name=F("method__name"), **splitter_fields)
            .annotate(**aggregations)
        )

        if not self.orderby_field:
            queryset = queryset.order_by(Lower("method_name"))

        return queryset


class TestMethodResultFilterSet(
    BuildFlowFilterSet, django_filters.rest_framework.FilterSet
):
    method_name = TestMethodPerfFilterSet.get_filters()["method_name"]

    dummy = TestMethodPerfFilterSet.dummy

    # this field should be renamed. These aren't really metrics.
    metrics = {
        "method_name": FieldType("Method Name", F("method_name")),
        "duration": FieldType("Duration", F("duration")),
        "cpu_usage": FieldType("CPU Usage", F("test_cpu_time_used")),
        "outcome": FieldType("Failures", F("outcome")),
        "id": FieldType("Id", F("id")),
        "date": FieldType("Date", F("build_flow__time_end")),
        "type": FieldType("Type", F("method__testclass__test_type")),
    }

    metric_choices = tuple((key, field.label) for key, field in metrics.items())
    includable_fields = metric_choices + tuple(
        zip(
            BuildFlowFilterSet.build_fields.keys(),
            BuildFlowFilterSet.build_fields.keys(),
        )
    )

    include_fields = django_filters.rest_framework.MultipleChoiceFilter(
        label="Include (multi-select okay)",
        choices=includable_fields,
        method=dummy,
        initial=["repo", "duration"],
    )

    ordering_fields = [(key, key) for (key, field) in includable_fields]

    o = django_filters.rest_framework.OrderingFilter(fields=ordering_fields)
    ordering_param_name = "o"


class TestMethodResultListView(TestMethodPerfListView):
    serializer_class = SimpleDictSerializer
    filter_backends = (django_filters.rest_framework.DjangoFilterBackend,)
    filterset_class = TestMethodResultFilterSet
    pagination_class = StandardResultsSetPagination
    ordering_param_name = filterset_class.ordering_param_name


# A bit of hackery to make a dynamic docstring, because the docstring
# appears in the UI.
TestMethodPerfListView.__doc__ = TestMethodPerfListView.__doc__.replace(
    "DEFAULTS.build_flows_limit", str(DEFAULTS.build_flows_limit)
)
