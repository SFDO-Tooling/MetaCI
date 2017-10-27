from django.shortcuts import render
from mrbelvedereci.api.serializers.cumulusci import OrgSerializer
from mrbelvedereci.api.serializers.cumulusci import ScratchOrgInstanceSerializer
from mrbelvedereci.api.serializers.cumulusci import ServiceSerializer
from mrbelvedereci.cumulusci.filters import OrgFilter
from mrbelvedereci.cumulusci.filters import ScratchOrgInstanceFilter
from mrbelvedereci.cumulusci.models import Org
from mrbelvedereci.cumulusci.models import ScratchOrgInstance
from mrbelvedereci.cumulusci.models import Service
from rest_framework import viewsets

class OrgViewSet(viewsets.ModelViewSet):
    """
    A viewset for viewing and editing Orgs
    """
    serializer_class = OrgSerializer
    queryset = Org.objects.all()
    filter_class = OrgFilter

class ScratchOrgInstanceViewSet(viewsets.ModelViewSet):
    """
    A viewset for viewing and editing ScratchOrgInstances
    """
    serializer_class = ScratchOrgInstanceSerializer
    queryset = ScratchOrgInstance.objects.all()
    filter_class = ScratchOrgInstanceFilter

class ServiceViewSet(viewsets.ModelViewSet):
    """
    A viewset for viewing and editing Services
    """
    serializer_class = ServiceSerializer
    queryset = Service.objects.all()
