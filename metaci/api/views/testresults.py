import django_filters.rest_framework
from django.db.models import F

from metaci.testresults.models import FieldType

from .testmethod_perf import BuildFlowFilterSet, TestMethodPerfFilterSet


class TestMethodResultFilterSet(
    BuildFlowFilterSet, django_filters.rest_framework.FilterSet
):
    """Filterset for individual unaggregated test results."""

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
        initial=["repo", "duration_average"],
    )

    ordering_fields = [(key, key) for (key, field) in includable_fields]

    o = django_filters.rest_framework.OrderingFilter(fields=ordering_fields)
    ordering_param_name = "o"
