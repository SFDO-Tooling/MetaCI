from django.shortcuts import render
from mrbelvedereci.api.pagination import RestrictedPagination
from mrbelvedereci.api.serializers.build import BuildSerializer
from mrbelvedereci.api.serializers.build import BuildFlowSerializer
from mrbelvedereci.api.serializers.build import RebuildSerializer
from mrbelvedereci.build.filters import BuildFilter
from mrbelvedereci.build.filters import BuildFlowFilter
from mrbelvedereci.build.filters import RebuildFilter
from mrbelvedereci.build.models import Build
from mrbelvedereci.build.models import BuildFlow
from mrbelvedereci.build.models import Rebuild
from rest_framework import viewsets

# mrbelvedereci.build
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
