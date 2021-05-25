from django.shortcuts import render
from rest_framework import viewsets

from metaci.api.serializers.plan import PlanRepositorySerializer, PlanSerializer
from metaci.plan.filters import PlanFilter, PlanRepositoryFilter
from metaci.plan.models import Plan, PlanRepository


class PlanViewSet(viewsets.ModelViewSet):
    """
    A viewset for viewing and editing plans
    """

    serializer_class = PlanSerializer
    queryset = Plan.objects.all()
    filterset_class = PlanFilter


class PlanRepositoryViewSet(viewsets.ModelViewSet):
    """
    A viewset for viewing and editing planrepositories
    """

    serializer_class = PlanRepositorySerializer
    queryset = PlanRepository.objects.all()
    filterset_class = PlanRepositoryFilter
