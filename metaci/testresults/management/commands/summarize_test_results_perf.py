import datetime

from django.core.management.base import BaseCommand
from metaci.testresults.models import TestResultPerfWeeklySummary
from metaci.api.views.testmethod_perf import TestMethodPerfFilterSet

DATE_FORMAT = "%Y-%m-%d"


def date_range(startString, endString, step):
    start = datetime.datetime.strptime(startString, DATE_FORMAT)
    end = datetime.datetime.strptime(endString, DATE_FORMAT)
    date_generated = (
        start + datetime.timedelta(days=x) for x in range(0, (end - start).days, 7)
    )

    for date in date_generated:
        yield date


class Command(BaseCommand):
    # NOTE: This should only be run at heroku postdeploy stage
    help = "Build rows in testresult_perfsummaries table for a single date"
    metrics = {
        name: f.aggregation for (name, f) in TestMethodPerfFilterSet.metrics.items()
    }
    annotations = [
        "count",
        "duration_average",
        "duration_slow",
        "duration_fast",
        "cpu_usage_average",
        "cpu_usage_low",
        "cpu_usage_high",
        "failures",
        "assertion_failures",
        "DML_failures",
        "Other_failures",
        "success_percentage",
    ]

    def add_arguments(self, parser):
        parser.add_argument("startdate", type=str)
        parser.add_argument("enddate", type=str)
        parser.add_argument("replace", choices=["replace", "continue"])

    def handle(self, startdate, enddate, replace, **options):
        should_replace = replace == "replace"
        if not should_replace:
            try:
                last_day_processed = TestResultPerfWeeklySummary.objects.order_by(
                    "-day"
                )[0].day
                # replace last day processed even if mode is not "replace".
                # often we won't have a way of knowing if the last day is
                # complete
                startdate = max(startdate, last_day_processed.strftime(DATE_FORMAT))
            except IndexError:
                pass
        dates = date_range(startdate, enddate, 7)
        for date in dates:
            TestResultPerfWeeklySummary.summarize_week(date)
