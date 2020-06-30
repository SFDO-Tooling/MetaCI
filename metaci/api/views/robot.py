from rest_framework.renderers import JSONRenderer, BrowsableAPIRenderer
from rest_framework import viewsets
from django_filters.rest_framework import DjangoFilterBackend
from metaci.api.renderers import SimpleCSVRenderer
from metaci.api.serializers.robot import RobotTestResultSerializer
from metaci.testresults.models import TestResult
from metaci.testresults.filters import RobotResultFilter
from rest_framework.filters import OrderingFilter


class RobotTestResultViewSet(viewsets.ReadOnlyModelViewSet):
    """
    A viewset for viewing robot framework test results
    """

    serializer_class = RobotTestResultSerializer
    renderer_classes = [BrowsableAPIRenderer, JSONRenderer, SimpleCSVRenderer]
    filterset_class = RobotResultFilter

    def get_queryset(self):
        queryset = TestResult.objects.filter(method__testclass__test_type="Robot")

        # FIXME: I'd like the user to be able to specify a period
        # of time such as "last two weeks" or "this month"...
        # I also need to

        # this is probably not the best default, but it's
        # good enough for now. Eventually I should add django's
        # ordering filter.
        sort = self.request.query_params.get("sort", "id").split(",")
        queryset = queryset.order_by(*sort)

        return queryset
