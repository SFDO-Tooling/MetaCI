from django.shortcuts import render
from metaci.api.serializers.plan import PlanSerializer
from metaci.plan.filters import PlanFilter
from metaci.plan.models import Plan
from rest_framework import viewsets

class PlanViewSet(viewsets.ModelViewSet):
    """
    A viewset for viewing and editing plans
    """
    serializer_class = PlanSerializer
    queryset = Plan.objects.all()
    filter_class = PlanFilter
