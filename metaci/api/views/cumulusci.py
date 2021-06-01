from django.shortcuts import render
from rest_framework import viewsets

from metaci.api.serializers.cumulusci import (
    OrgSerializer,
    ScratchOrgInstanceSerializer,
    ServiceSerializer,
)
from metaci.cumulusci.filters import OrgFilter, ScratchOrgInstanceFilter
from metaci.cumulusci.models import Org, ScratchOrgInstance, Service


class OrgViewSet(viewsets.ModelViewSet):
    """
    A viewset for viewing and editing Orgs
    """

    serializer_class = OrgSerializer
    queryset = Org.objects.all()
    filterset_class = OrgFilter


class ScratchOrgInstanceViewSet(viewsets.ModelViewSet):
    """
    A viewset for viewing and editing ScratchOrgInstances
    """

    serializer_class = ScratchOrgInstanceSerializer
    queryset = ScratchOrgInstance.objects.all()
    filterset_class = ScratchOrgInstanceFilter


class ServiceViewSet(viewsets.ModelViewSet):
    """
    A viewset for viewing and editing Services
    """

    serializer_class = ServiceSerializer
    queryset = Service.objects.all()
