from django.shortcuts import render
from metaci.api.pagination import RestrictedPagination
from metaci.api.serializers.build import BuildSerializer
from metaci.api.serializers.build import BuildFlowSerializer
from metaci.api.serializers.build import RebuildSerializer
from metaci.build.filters import BuildFilter
from metaci.build.filters import BuildFlowFilter
from metaci.build.filters import RebuildFilter
from metaci.build.models import Build
from metaci.build.models import BuildFlow
from metaci.build.models import Rebuild
from rest_framework import viewsets

class BuildViewSet(viewsets.ModelViewSet):
    """
    A viewset for viewing and editing builds
    """
    serializer_class = BuildSerializer
    queryset = Build.objects.all()
    filter_class = BuildFilter
    pagination_class = RestrictedPagination

class BuildFlowViewSet(viewsets.ModelViewSet):
    """
    a viewset for viewing and editing build flows
    """
    serializer_class = BuildFlowSerializer
    queryset = BuildFlow.objects.all()
    filter_class = BuildFlowFilter

class RebuildViewSet(viewsets.ModelViewSet):
    """
    a viewset for viewing and editing rebuilds
    """
    serializer_class = RebuildSerializer
    queryset = Rebuild.objects.all()
    filter_class = RebuildFilter
