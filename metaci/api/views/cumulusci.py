from django.contrib.auth import get_user_model
from metaci.api.serializers.cumulusci import OrgSerializer, RegisteredOrgSerializer
from metaci.api.serializers.cumulusci import ScratchOrgInstanceSerializer
from metaci.api.serializers.cumulusci import ServiceSerializer
from metaci.cumulusci.filters import OrgFilter, RegisteredOrgFilter
from metaci.cumulusci.filters import ScratchOrgInstanceFilter
from metaci.cumulusci.models import Org
from metaci.cumulusci.models import ScratchOrgInstance
from metaci.cumulusci.models import Service
from rest_framework import viewsets

class OrgViewSet(viewsets.ModelViewSet):
    """
    A viewset for viewing and editing Orgs
    """
    serializer_class = OrgSerializer
    queryset = Org.ci_orgs.all()
    filter_class = OrgFilter

class RegisteredOrgViewSet(viewsets.ModelViewSet):
    """
    A viewset for viewing and editing Registered Orgs
    """
    serializer_class = RegisteredOrgSerializer
    queryset = Org.registered_orgs.all()
    filter_class = RegisteredOrgFilter

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
