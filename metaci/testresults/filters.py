import django_filters
from django_filters.widgets import RangeWidget

from metaci.build.models import BuildFlow

class BuildFlowFilter(django_filters.FilterSet):
    plan = django_filters.CharFilter(name="build__plan__name", label='Plan Name', lookup_expr='contains')
    branch = django_filters.CharFilter(name="build__branch__name", label='Branch Name', lookup_expr='contains')
    build = django_filters.CharFilter(name='build')
    start_date = django_filters.DateFromToRangeFilter(name="build__time_start", label="Start Date",widget=RangeWidget(attrs={'placeholder': 'MM/DD/YYYY'}))

    class Meta:
        model = BuildFlow
        fields = ['build','plan','branch','start_date']
