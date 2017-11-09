from metaci.api.serializers.repository import BranchSerializer
from metaci.api.serializers.repository import RepositorySerializer
from metaci.repository.filters import BranchFilter
from metaci.repository.filters import RepositoryFilter
from metaci.repository.models import Branch
from metaci.repository.models import Repository
from metaci.api.utils import PkOrSlugMixin
from rest_framework import viewsets

class BranchViewSet(viewsets.ModelViewSet):
    """
    A viewset for viewing and editing Branch instances.
    """
    serializer_class = BranchSerializer
    queryset = Branch.objects.all()
    filter_class = BranchFilter

class RepositoryViewSet(PkOrSlugMixin, viewsets.ModelViewSet):
    """
    A viewset for viewing and editing Repo instances.
    """
    serializer_class = RepositorySerializer
    queryset = Repository.objects.all()
    filter_class = RepositoryFilter
    lookup_slug_field = 'name'
