import datetime

import dateutil.parser
from django.utils import timezone
from rest_framework import viewsets
from rest_framework.renderers import BrowsableAPIRenderer, JSONRenderer

from metaci.api.renderers.csv_renderer import SimpleCSVRenderer
from metaci.api.serializers.robot import RobotTestResultSerializer
from metaci.build.models import BuildFlow
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
        """Return a query set for robot results

        'from' and 'to' query parameters can be used to constrain
        the results. If not provided results for the current day will
        be returned.

        This code uses dateutil.parser.parse to conver the parameters
        to dates, and then adjusts them to midnight and for the current
        timezone (timezone.get_current_timezone()).

        In the following example, results will be returnd for the entire
        month of April, 2020:

            /api/robot?from=2020-04-01&to=2020-04-30

        """
        from_ = self.request.query_params.get("from", "00:00:00")
        start_date = dateutil.parser.parse(from_)
        start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
        start_date = timezone.make_aware(start_date, timezone.get_current_timezone())

        to_ = self.request.query_params.get("to", from_)
        end_date = dateutil.parser.parse(to_) + datetime.timedelta(days=1)
        end_date = end_date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_date = timezone.make_aware(end_date, timezone.get_current_timezone())

        # Should I be kinder and gentler here, and simply swap the dates?
        assert start_date <= end_date

        buildflows = BuildFlow.objects.filter(
            time_end__date__gte=start_date, time_end__date__lt=end_date
        )

        queryset = (
            TestResult.objects.filter(
                method__testclass__test_type="Robot", build_flow_id__in=buildflows,
            )
            .prefetch_related(
                "build_flow__build__branch",
                "build_flow__build__repo",
                "method__testclass",
            )
            .order_by("build_flow__time_end")
        )

        return queryset
