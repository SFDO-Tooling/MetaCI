from rest_framework import viewsets

from metaci.api.serializers.repository import BranchSerializer, RepositorySerializer
from metaci.api.utils import PkOrSlugMixin
from metaci.repository.filters import BranchFilter, RepositoryFilter
from metaci.repository.models import Branch, Repository


class BranchViewSet(viewsets.ModelViewSet):
    """
    A viewset for viewing and editing Branch instances.
    """

    serializer_class = BranchSerializer
    queryset = Branch.objects.all()
    filterset_class = BranchFilter


class RepositoryViewSet(PkOrSlugMixin, viewsets.ModelViewSet):
    """
    A viewset for viewing and editing Repo instances.
    """

    serializer_class = RepositorySerializer
    queryset = Repository.objects.all()
    filterset_class = RepositoryFilter
    lookup_slug_field = "name"
