from django.shortcuts import render
from mrbelvedereci.api.serializers.repository import BranchSerializer
from mrbelvedereci.api.serializers.repository import RepositorySerializer
from mrbelvedereci.repository.filters import BranchFilter
from mrbelvedereci.repository.filters import RepositoryFilter
from mrbelvedereci.repository.models import Branch
from mrbelvedereci.repository.models import Repository
from rest_framework import viewsets

class BranchViewSet(viewsets.ModelViewSet):
    """
    A viewset for viewing and editing user instances.
    """
    serializer_class = BranchSerializer
    queryset = Branch.objects.all()
    filter_class = BranchFilter

class RepositoryViewSet(viewsets.ModelViewSet):
    """
    A viewset for viewing and editing user instances.
    """
    serializer_class = RepositorySerializer
    queryset = Repository.objects.all()
    filter_class = RepositoryFilter
