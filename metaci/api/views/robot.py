from rest_framework.renderers import JSONRenderer, BrowsableAPIRenderer
from rest_framework import viewsets
from metaci.api.renderers import SimpleCSVRenderer
from metaci.api.serializers.robot import RobotTestResultSerializer
from metaci.testresults.models import TestResult


class RobotTestResultViewSet(viewsets.ReadOnlyModelViewSet):
    """
    A viewset for viewing robot framework test results
    """

    serializer_class = RobotTestResultSerializer
    renderer_classes = [BrowsableAPIRenderer, JSONRenderer, SimpleCSVRenderer]

    def get_queryset(self):
        queryset = TestResult.objects.all()
        repo = self.request.query_params.get("repo", None)
        if repo is not None:
            queryset = queryset.filter(build_flow__build__repo__name=repo)

        sort = self.request.query_params.get("sort", "id").split(",")
        queryset = queryset.order_by(*sort)

        # FIXME: I'd like the user to be able to specify a period
        # of time such as "last two weeks" or "this month"...
        return queryset
