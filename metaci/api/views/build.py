from django.shortcuts import render
from rest_framework import viewsets

from metaci.api.pagination import RestrictedPagination
from metaci.api.serializers.build import (
    BuildFlowSerializer,
    BuildSerializer,
    RebuildSerializer,
)
from metaci.build.filters import BuildFilter, BuildFlowFilter, RebuildFilter
from metaci.build.models import Build, BuildFlow, Rebuild


class BuildViewSet(viewsets.ModelViewSet):
    """
    A viewset for viewing and editing builds
    """

    serializer_class = BuildSerializer
    queryset = Build.objects.all()
    filterset_class = BuildFilter
    pagination_class = RestrictedPagination


class BuildFlowViewSet(viewsets.ModelViewSet):
    """
    a viewset for viewing and editing build flows
    """

    serializer_class = BuildFlowSerializer
    queryset = BuildFlow.objects.all()
    filterset_class = BuildFlowFilter


class RebuildViewSet(viewsets.ModelViewSet):
    """
    a viewset for viewing and editing rebuilds
    """

    serializer_class = RebuildSerializer
    queryset = Rebuild.objects.all()
    filterset_class = RebuildFilter
