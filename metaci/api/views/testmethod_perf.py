from datetime import datetime, timedelta

import django_filters.rest_framework
from django.db import connection
from django.db.models import BigIntegerField, F, FloatField, Sum
from django.db.models.functions import Cast
from django_filters.widgets import DateRangeWidget
from rest_framework import exceptions, generics, pagination, permissions, viewsets

from metaci.api.serializers.simple_dict_serializer import SimpleDictSerializer
from metaci.plan.models import Plan
from metaci.repository.models import Branch, Repository
from metaci.testresults.models import FieldType, TestResultPerfWeeklySummary

thirty_days_ago = datetime.now() - timedelta(days=30)


class DEFAULTS:
    page_size = 50
    max_page_size = 100
    branch = "main"
    daterange_after = thirty_days_ago.isoformat("T").split("T")[0]


def set_timeout(timeout):
    """Restrict extremely long Postgres queries.

    Theoretically this should reset on the next request but that
    could use some additional testing.
    """
    with connection.cursor() as cursor:
        cursor.execute("SET LOCAL statement_timeout=%s", [timeout * 1000])


class StandardResultsSetPagination(pagination.PageNumberPagination):
    page_size = DEFAULTS.page_size
    page_size_query_param = "page_size"
    max_page_size = DEFAULTS.max_page_size


class BuildFlowFilterSet(django_filters.rest_framework.FilterSet):
    """A "conditional" filterset for generating the BuildFlow sub-select.

    The tricky bit is that this filter serves three different jobs.

    1. It validates incoming parameters (which is not strictly necessary
        but probably difficult to turn off and perhaps sometimes useful).

    2. It populates the django-filter form.

    3. It drives actual filtering of the build-list sub-query.
    """

    repo_choices = (
        Repository.objects.values_list("name", "name").order_by("name").distinct()
    )

    repo = django_filters.rest_framework.ChoiceFilter(
        field_name="rel_repo__name", label="Repo Name", choices=repo_choices
    )

    branch = django_filters.rest_framework.CharFilter(
        field_name="rel_branch__name", label="Branch Name"
    )

    plan_choices = Plan.objects.values_list("name", "name").order_by("name").distinct()
    plan = django_filters.rest_framework.ChoiceFilter(
        field_name="rel_plan__name", label="Plan Name", choices=plan_choices
    )

    # Django-filter's DateRangeFilter is kind of ... special
    # disable until we can fix it.
    #
    # recentdate = DateRangeFilter(label="Recent Date", field_name="time_end")
    # disable_by_default.append("recentdate")

    daterange = django_filters.rest_framework.DateFromToRangeFilter(
        field_name="week_start",
        label="Date range",
        widget=DateRangeWidget(attrs={"type": "date"}),
    )

    def dummy_filter(self, queryset, name, value):
        return queryset

    fields_and_stuff = locals()

    build_fields = {}

    for name in ("repo", "plan", "branch"):
        # make a list of db field_names for use in grouping
        build_fields[name] = fields_and_stuff[name].field_name


def dynamicBuildFlowFilterSetBuilder(repo_name):
    class DynamicBuildFlowFilterSet(BuildFlowFilterSet):
        if repo_name:
            branches = (
                Branch.include_deleted.filter(repo__name=repo_name)
                .values_list("name", "name")
                .order_by("name")
                .distinct()
            )
            branch = django_filters.rest_framework.ChoiceFilter(
                field_name="rel_branch__name",
                label="Branch Name",
                choices=list(branches),
            )

    return DynamicBuildFlowFilterSet


def AsInt(expr):
    return Cast(expr, BigIntegerField())


def AsFloat(expr):
    return Cast(expr, FloatField())


def AvgofAvgs(fieldname):
    return AsFloat(Sum(AsInt(F(fieldname) * F("agg_count"))) / Sum("agg_count"))


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

    metrics = {
        "method_name": FieldType("Method Name", F("method__name")),
        "duration_average": FieldType(
            "Duration: Average", AvgofAvgs("agg_duration_average")
        ),
        "duration_slow": FieldType("Duration: Slow", AvgofAvgs("agg_duration_slow")),
        "duration_fast": FieldType("Duration: Fast", AvgofAvgs("agg_duration_fast")),
        "cpu_usage_average": FieldType(
            "CPU Usage: Average", AvgofAvgs("agg_cpu_usage_average")
        ),
        "cpu_usage_low": FieldType("CPU Usage: Low", AvgofAvgs("agg_cpu_usage_low")),
        "cpu_usage_high": FieldType("CPU Usage: High", AvgofAvgs("agg_cpu_usage_high")),
        "count": FieldType("Count", Sum(F("agg_count"))),
        "failures": FieldType("Failures", Sum("agg_failures")),
        "assertion_failures": FieldType(
            "Assertion Failures", Sum("agg_assertion_failures")
        ),
        "success_percentage": FieldType(
            "Success Percentage",
            AsInt(
                (AsFloat(Sum(F("agg_count"))) - Sum(F("agg_failures")))
                / AsFloat(Sum(F("agg_count")))
                * 100
            ),
        ),
        "DML_failures": FieldType("DML Failures", Sum("agg_DML_failures")),
        "other_failures": FieldType("Other Failures", Sum("agg_other_failures")),
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

    ordering_fields = tuple((name, name) for (name, label) in includable_fields)
    ordering_fields += ("method_name", "method_name")
    o = django_filters.rest_framework.OrderingFilter(fields=ordering_fields)
    ordering_param_name = "o"


class MetaCIApiException(exceptions.APIException):
    status_code = 400
    default_detail = "Validation Error."
    default_code = 400


class TestMethodPerfListView(generics.ListAPIView, viewsets.ViewSet):
    """A view for lists of aggregated test metrics."""

    serializer_class = SimpleDictSerializer
    filter_backends = (django_filters.rest_framework.DjangoFilterBackend,)
    filterset_class = TestMethodPerfFilterSet
    pagination_class = StandardResultsSetPagination
    ordering_param_name = filterset_class.ordering_param_name
    permission_classes = (permissions.AllowAny,)
    model_fields = set(
        field.name for field in TestResultPerfWeeklySummary._meta.get_fields()
    )

    # example URLs:
    # http://localhost:8000/api/testmethod_perf/?repo=gem&plan=Release%20Test&method_name=testCreateNegative
    # http://localhost:8000/api/testmethod_perf/?repo=Cumulus&plan=Feature%20Test&o=avg
    # http://localhost:8000/api/testmethod_perf/?method_name=&repo=&plan=&flow=&recentdate=&daterange_after=&daterange_before=&o=-repo

    @property
    def orderby_field(self):
        return self.request.query_params.get(self.ordering_param_name)

    def _get_aggregation_fields(self):
        """What fields should appear in the output?"""
        params = self.request.query_params
        aggregations = {}

        fields_to_include = params.getlist("include_fields")
        filters = self.filterset_class.get_filters()
        fields = self.filterset_class.metrics

        # every field we want to filter on should be in the annotation list
        for param, value in params.items():
            if value and (
                filters.get(param)  # param is a filter, not a random config
                and filters[param].field_name  # safety check
                and param != "method_name"  # automatically included already
                and fields.get(filters[param].field_name)  # param has associated field
            ):
                fields_to_include.append(filters[param].field_name)

        # no fields? Use defaults
        if fields_to_include == []:
            filters = self.filterset_class.get_filters()
            assert filters
            include_filter = filters["include_fields"]
            assert include_filter
            default_include_fields = include_filter.extra["initial"]
            assert default_include_fields

            fields_to_include.extend(default_include_fields)

        # the field we want to order on should be in the annotation list
        if self.orderby_field and self.orderby_field.strip("-") != "method_name":
            fields_to_include.append(self.orderby_field.strip("-"))

        # build a dictionary in the form DRF likes
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
                output_fields[param] = F(build_fields[param])

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
        set_timeout(30)
        self._check_params()

        splitter_fields = self._get_splitter_fields()
        aggregations = self._get_aggregation_fields()

        queryset = (
            TestResultPerfWeeklySummary.objects.for_user(self.request.user)
            .values(method_name=F("method__name"), **splitter_fields)
            .annotate(**aggregations)
        )

        if not self.orderby_field:
            queryset = queryset.order_by("method_name")

        return queryset
