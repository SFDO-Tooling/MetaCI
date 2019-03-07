import copy

from django.shortcuts import render
from django.db.models import F, Avg, Count, Q
from django.db import models
from django.forms import SelectDateWidget, DateInput

import django_filters.rest_framework
from django_filters.widgets import DateRangeWidget, SuffixedMultiWidget
from django_filters.rest_framework import DateRangeFilter

from rest_framework import generics, filters, exceptions

from metaci.testresults.models import TestResult
from metaci.build.models import BuildFlow
from metaci.build.filters import BuildFilter
from metaci.api.serializers.testmethod_perf import TestMethodPerfSerializer
from metaci.repository.models import Repository, Branch
from metaci.plan.models import Plan

from django.db import connection


def set_timeout(timeout):
    with connection.cursor() as cursor:
        cursor.execute("SET LOCAL statement_timeout=%s", [timeout * 1000])


class TurnFilterSetOffByDefaultBase(django_filters.rest_framework.FilterSet):
    really_filter = False

    def __init__(self, *args, really_filter=really_filter, **kwargs):
        self.really_filter = really_filter
        super().__init__(*args, **kwargs)

        for filtername in self.filters.keys():
            if not really_filter and filtername in BuildFlowFilterSet.__dict__.keys():
                print(self.filters[filtername])
                self.filters[filtername] = copy.copy(self.filters[filtername])
                self.filters[filtername].method = self.dummy_filter

    def dummy_filter(self, queryset, name, value):
        return queryset


class BuildFlowFilterSet(TurnFilterSetOffByDefaultBase):
    """This filterset is not used directly on the output queryset.
       get_queryset must create it explicitly with really_filter=True."""

    param_filters = {
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
        label="Date range", widget=DateRangeWidget(attrs={"type": "date"})
    )

    # This is not really a filter. It's actually just a query input but putting it
    # here lets me get it in the form.
    build_flows_limit = django_filters.rest_framework.NumberFilter(
        method="dummy_filter", label="Build Flows Limit (default: 100)"
    )


class TestMethodPerfFilter(BuildFlowFilterSet, django_filters.rest_framework.FilterSet):
    method_name = django_filters.rest_framework.CharFilter(
        field_name="method_name", label="Method Name"
    )

    dummy = lambda queryset, name, value: queryset
    group_by_choices = (
        ("repo", "repo"),
        ("plan", "plan"),
        ("flow", "flow"),
        ("branch", "branch"),
    )
    group_by = django_filters.rest_framework.MultipleChoiceFilter(
        label="Split On", choices=group_by_choices, method=dummy
    )

    o = django_filters.rest_framework.OrderingFilter(
        fields=(
            ("avg", "avg"),
            ("method_name", "method_name"),
            ("count", "count"),
            ("repo", "repo"),
            ("failures", "failures"),
            ("assertion_failures", "assertion_failures"),
            ("DML_failures", "DML_failures"),
            ("Other_failures", "Other_failures"),
        )
    )


BUILD_FLOWS_LIMIT = 100


class TestMethodPerfListView(generics.ListAPIView):
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

    def get_queryset(self):
        set_timeout(20)
        get = self.request.query_params.get

        build_flows_limit = int(get("build_flows_limit") or BUILD_FLOWS_LIMIT)

        print("GET", self.request.query_params)

        buildflows = BuildFlow.objects.filter(tests_total__isnull=False)
        buildflows = BuildFlowFilterSet(
            self.request.GET, buildflows, really_filter=True
        ).qs

        output_fields = {"repo": F("build_flow__build__repo__name")}

        param_filters = BuildFlowFilterSet.param_filters
        if get("group_by"):
            for param in self.request.query_params.getlist("group_by"):
                output_fields[param] = F("build_flow__" + param_filters[param])

        if get("recentdate") and (get("daterange_after") or get("daterange_before")):
            raise exceptions.APIException("Specified both recentdate and daterange")

        buildflows = buildflows.order_by("-time_end")[0:build_flows_limit]

        annotations = {"count": Count("id"), "avg": Avg("duration")}

        if get("o") and "failures" in get("o"):
            annotations.update(
                {
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
                }
            )

        queryset = (
            TestResult.objects.filter(
                build_flow_id__in=buildflows, duration__isnull=False
            )
            .values(method_name=F("method__name"), **output_fields)
            .annotate(**annotations)
        )

        return queryset


TestMethodPerfListView.__doc__ = TestMethodPerfListView.__doc__.replace(
    "BUILD_FLOWS_LIMIT", str(BUILD_FLOWS_LIMIT)
)
