from django_rq import job
from metaci.testresults.models import TestResultPerfWeeklySummary
from datetime import datetime, timedelta


@job
def generate_summaries():
    """ An RQ repeatable task to summarize test results for faster querying.
    """
    TestResultPerfWeeklySummary.summarize_week(datetime.now())
    is_sunday = datetime.now().weekday() == 6
    if is_sunday:
        a_day_last_week = datetime.now() - timedelta(days=2)
        TestResultPerfWeeklySummary.summarize_week(a_day_last_week)
