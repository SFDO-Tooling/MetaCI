from rest_framework import viewsets
from rest_framework.renderers import BrowsableAPIRenderer, JSONRenderer

from metaci.api.renderers.csv_renderer import SimpleCSVRenderer
from metaci.api.serializers.robot import RobotTestResultSerializer
from metaci.testresults.filters import RobotResultFilter
from metaci.testresults.models import TestResult


class RobotTestResultViewSet(viewsets.ReadOnlyModelViewSet):
    """
    A viewset for viewing robot framework test results
    """

    serializer_class = RobotTestResultSerializer
    renderer_classes = [BrowsableAPIRenderer, JSONRenderer, SimpleCSVRenderer]
    filterset_class = RobotResultFilter

    def get_queryset(self):
        queryset = TestResult.objects.filter(method__testclass__test_type="Robot")
        queryset = queryset.prefetch_related(
            "build_flow__build__branch", "build_flow__build__repo", "method__testclass",
        )

        # FIXME: I'd like the user to be able to specify a period
        # of time such as "last two weeks" or "this month"...
        # I also need to

        # this is probably not the best default, but it's
        # good enough for now. Eventually I should add django's
        # ordering filter.
        sort = self.request.query_params.get("sort", "id").split(",")
        queryset = queryset.order_by(*sort)

        return queryset
