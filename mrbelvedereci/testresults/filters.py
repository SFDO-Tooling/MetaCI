import django_filters

from mrbelvedereci.build.models import BuildFlow

class BuildFlowFilter(django_filters.FilterSet):
    plan = django_filters.CharFilter(name="build__plan__name", label='Plan Name', lookup_expr='contains')
    build = django_filters.CharFilter(name='build')

    class Meta:
        model = BuildFlow
        fields = ['build','plan']