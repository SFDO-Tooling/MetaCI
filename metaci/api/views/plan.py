from django.shortcuts import render
from metaci.api.serializers.plan import PlanSerializer
from metaci.api.serializers.plan import PlanRepositorySerializer
from metaci.plan.filters import PlanFilter
from metaci.plan.filters import PlanRepositoryFilter
from metaci.plan.models import Plan
from metaci.plan.models import PlanRepository
from rest_framework import viewsets

class PlanViewSet(viewsets.ModelViewSet):
    """
    A viewset for viewing and editing plans
    """
    serializer_class = PlanSerializer
    queryset = Plan.objects.all()
    filter_class = PlanFilter

class PlanRepositoryViewSet(viewsets.ModelViewSet):
    """
    A viewset for viewing and editing planrepositories
    """
    serializer_class = PlanRepositorySerializer
    queryset = PlanRepository.objects.all()
    filter_class = PlanRepositoryFilter
