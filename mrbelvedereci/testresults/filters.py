import django_filters

from mrbelvedereci.build.models import BuildFlow

class BuildFlowFilter(django_filters.FilterSet):
    flow_name = django_filters.CharFilter(name="flow__name")
    build = django_filters.CharFilter(name='build')

    class Meta:
        model = BuildFlow
        fields = ['build','flow_name']