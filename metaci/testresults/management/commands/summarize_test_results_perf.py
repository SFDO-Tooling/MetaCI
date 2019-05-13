from django.core.management.base import BaseCommand
from metaci.testresults.models import TestResultPerfWeeklySummary


class Command(BaseCommand):
    # NOTE: This should only be run at heroku postdeploy stage
    help = "Build rows in testresult_perfsummaries table for a single date"

    def add_arguments(self, parser):
        parser.add_argument("startdate", type=str)
        parser.add_argument("enddate", type=str)
        parser.add_argument("replace", choices=["replace", "continue"])

    def handle(self, startdate, enddate, replace, **options):
        DATE_FORMAT = "%Y-%m-%d"
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
        TestResultPerfWeeklySummary.summarize_weeks(startdate, enddate)
