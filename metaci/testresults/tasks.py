from django_rq import job
from metaci.testresults.models import TestResultPerfWeeklySummary


@job
def generate_summaries():
    """ An RQ repeatable task to summarize test results for faster querying.
    """
    TestResultPerfWeeklySummary.summarize_weeks()
