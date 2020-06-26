import django_filters
from django_filters.widgets import RangeWidget

from metaci.build.models import BuildFlow
from metaci.testresults.models import TestResult


class BuildFlowFilter(django_filters.FilterSet):
    plan = django_filters.CharFilter(
        field_name="build__plan__name", label="Plan Name", lookup_expr="contains"
    )
    branch = django_filters.CharFilter(
        field_name="build__branch__name", label="Branch Name", lookup_expr="contains"
    )
    build = django_filters.CharFilter(field_name="build")
    start_date = django_filters.DateFromToRangeFilter(
        field_name="build__time_start",
        label="Start Date",
        widget=RangeWidget(attrs={"placeholder": "MM/DD/YYYY"}),
    )

    class Meta:
        model = BuildFlow
        fields = ["build", "plan", "branch", "start_date"]


class RobotResultFilter(django_filters.FilterSet):
    repo_name = django_filters.CharFilter(
        field_name="build_flow__build__repo__name",
        label="Repository name",
        lookup_expr="iexact",
    )
    branch_name = django_filters.CharFilter(
        field_name="build_flow__build__branch__name",
        label="Branch name",
        lookup_expr="iexact",
    )
    test_name = django_filters.CharFilter(
        field_name="method__name", label="Test name", lookup_expr="iexact",
    )
    outcome = django_filters.CharFilter(
        field_name="outcome", label="Outcome", lookup_expr="iexact",
    )

    class Meta:
        model = TestResult
        fields = ["repo_name", "test_name", "outcome"]
