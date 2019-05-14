from django.core.management.base import BaseCommand
from metaci.testresults.models import TestResultPerfWeeklySummary


class Command(BaseCommand):
    # NOTE: This should only be run at heroku postdeploy stage
    help = "Build rows in testresult_perfsummaries table for a single date"

    def add_arguments(self, parser):
        parser.add_argument("startdate", type=str)
        parser.add_argument("enddate", type=str)

    def handle(self, startdate, enddate, replace, **options):
        TestResultPerfWeeklySummary.summarize_weeks(startdate, enddate)
