from __future__ import unicode_literals

import datetime
import logging
import os
from collections import OrderedDict, namedtuple

from dateutil.tz import gettz
from django.apps import apps
from django.db import models
from django.db.models import Aggregate, Avg, Count, F, FloatField, Q, StdDev, Value
from django.db.models.functions import Cast
from django.urls import reverse
from django.utils import timezone

from metaci.build import models as build_models
from metaci.testresults.choices import OUTCOME_CHOICES, TEST_TYPE_CHOICES
from metaci.utils import split_seq


class TestClass(models.Model):
    name = models.CharField(max_length=255, db_index=True)
    test_type = models.CharField(
        max_length=32, choices=TEST_TYPE_CHOICES, db_index=True
    )
    repo = models.ForeignKey(
        "repository.Repository", related_name="testclasses", on_delete=models.CASCADE
    )

    class Meta:
        verbose_name = "Test Class"
        verbose_name_plural = "Test Classes"

    def __str__(self):
        return self.name

    # pytest: this is not a test
    __test__ = False


class TestMethod(models.Model):
    name = models.CharField(max_length=255, db_index=True)
    testclass = models.ForeignKey(
        TestClass, related_name="methods", on_delete=models.CASCADE
    )
    test_dashboard = models.BooleanField(default=False)
    description = models.CharField(max_length=1024, null=True, blank=True)

    class Meta:
        verbose_name = "Test Method"

    def __str__(self):
        return self.name

    # pytest: This is not a test
    __test__ = False


class TestResultManager(models.Manager):
    def update_summary_fields(self):
        for summary in self.all():
            summary.update_summary_fields()

    def compare_results(self, build_flows):

        results = OrderedDict()
        for build_flow in build_flows:
            test_results = (
                build_flow.test_results.select_related("method")
                .select_related("method__testclass")
                .all()
            )
            for result in test_results:
                cls = result.method.testclass.name
                method = result.method.name

                if cls not in results:
                    results[cls] = OrderedDict()

                if method not in results[cls]:
                    results[cls][method] = {}

                for limit in result.get_limit_types():
                    test_limit = f"test_{limit}_used"

                    if test_limit not in results[cls][method]:
                        results[cls][method][test_limit] = OrderedDict()

                    results[cls][method][test_limit][build_flow.id] = getattr(
                        result, test_limit
                    )

        diff = OrderedDict()

        for cls, methods in results.items():
            for method, limits in methods.items():
                for limit, build_flows in limits.items():
                    # Are any values different between the build_flows?
                    if len(set(build_flows.values())) > 1:
                        if cls not in diff:
                            diff[cls] = OrderedDict()

                        if method not in diff[cls]:
                            diff[cls][method] = {}

                        if limit not in diff[cls][method]:
                            diff[cls][method][limit] = OrderedDict()

                        diff[cls][method][limit] = build_flows

        return diff


class TestResult(models.Model):
    __test__ = False  # keep pytest from whining

    build_flow = models.ForeignKey(
        "build.BuildFlow", related_name="test_results", on_delete=models.CASCADE
    )
    method = models.ForeignKey(
        TestMethod, related_name="test_results", on_delete=models.CASCADE
    )
    # NOTE: This field is currently only populated for robot tasks
    # The task field is used to reconstitute the test log, which is
    # needed because the task has a list of options used by robot when
    # the test was run (e.g. noncritical, tagstatlink, etc)
    task = models.ForeignKey(
        "build.FlowTask",
        related_name="test_results",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        default=None,
        help_text="Task which generated the original output.xml file",
    )
    duration = models.FloatField(null=True, blank=True, db_index=True)
    outcome = models.CharField(max_length=16, choices=OUTCOME_CHOICES, db_index=True)
    stacktrace = models.TextField(null=True, blank=True)
    message = models.TextField(null=True, blank=True)
    source_file = models.CharField(max_length=255)
    # robot_keyword will be used to store the first keyword that failed in
    # a failing test.
    robot_keyword = models.CharField(
        max_length=255, null=True, blank=True, db_index=True
    )
    robot_tags = models.TextField(null=True, blank=True)
    robot_xml = models.TextField(null=True, blank=True)
    email_invocations_used = models.IntegerField(null=True, blank=True)
    email_invocations_allowed = models.IntegerField(null=True, blank=True)
    email_invocations_percent = models.IntegerField(null=True, blank=True)
    soql_queries_used = models.IntegerField(null=True, blank=True)
    soql_queries_allowed = models.IntegerField(null=True, blank=True)
    soql_queries_percent = models.IntegerField(null=True, blank=True)
    future_calls_used = models.IntegerField(null=True, blank=True)
    future_calls_allowed = models.IntegerField(null=True, blank=True)
    future_calls_percent = models.IntegerField(null=True, blank=True)
    dml_rows_used = models.IntegerField(null=True, blank=True)
    dml_rows_allowed = models.IntegerField(null=True, blank=True)
    dml_rows_percent = models.IntegerField(null=True, blank=True)
    cpu_time_used = models.IntegerField(null=True, blank=True)
    cpu_time_allowed = models.IntegerField(null=True, blank=True)
    cpu_time_percent = models.IntegerField(null=True, blank=True)
    query_rows_used = models.IntegerField(null=True, blank=True)
    query_rows_allowed = models.IntegerField(null=True, blank=True)
    query_rows_percent = models.IntegerField(null=True, blank=True)
    dml_statements_used = models.IntegerField(null=True, blank=True)
    dml_statements_allowed = models.IntegerField(null=True, blank=True)
    dml_statements_percent = models.IntegerField(null=True, blank=True)
    mobile_apex_push_used = models.IntegerField(null=True, blank=True)
    mobile_apex_push_allowed = models.IntegerField(null=True, blank=True)
    mobile_apex_push_percent = models.IntegerField(null=True, blank=True)
    heap_size_used = models.IntegerField(null=True, blank=True)
    heap_size_allowed = models.IntegerField(null=True, blank=True)
    heap_size_percent = models.IntegerField(null=True, blank=True)
    sosl_queries_used = models.IntegerField(null=True, blank=True)
    sosl_queries_allowed = models.IntegerField(null=True, blank=True)
    sosl_queries_percent = models.IntegerField(null=True, blank=True)
    queueable_jobs_used = models.IntegerField(null=True, blank=True)
    queueable_jobs_allowed = models.IntegerField(null=True, blank=True)
    queueable_jobs_percent = models.IntegerField(null=True, blank=True)
    callouts_used = models.IntegerField(null=True, blank=True)
    callouts_allowed = models.IntegerField(null=True, blank=True)
    callouts_percent = models.IntegerField(null=True, blank=True)
    test_email_invocations_used = models.IntegerField(null=True, blank=True)
    test_email_invocations_allowed = models.IntegerField(null=True, blank=True)
    test_email_invocations_percent = models.IntegerField(null=True, blank=True)
    test_soql_queries_used = models.IntegerField(null=True, blank=True)
    test_soql_queries_allowed = models.IntegerField(null=True, blank=True)
    test_soql_queries_percent = models.IntegerField(null=True, blank=True)
    test_future_calls_used = models.IntegerField(null=True, blank=True)
    test_future_calls_allowed = models.IntegerField(null=True, blank=True)
    test_future_calls_percent = models.IntegerField(null=True, blank=True)
    test_dml_rows_used = models.IntegerField(null=True, blank=True)
    test_dml_rows_allowed = models.IntegerField(null=True, blank=True)
    test_dml_rows_percent = models.IntegerField(null=True, blank=True)
    test_cpu_time_used = models.IntegerField(null=True, blank=True)
    test_cpu_time_allowed = models.IntegerField(null=True, blank=True)
    test_cpu_time_percent = models.IntegerField(null=True, blank=True)
    test_query_rows_used = models.IntegerField(null=True, blank=True)
    test_query_rows_allowed = models.IntegerField(null=True, blank=True)
    test_query_rows_percent = models.IntegerField(null=True, blank=True)
    test_dml_statements_used = models.IntegerField(null=True, blank=True)
    test_dml_statements_allowed = models.IntegerField(null=True, blank=True)
    test_dml_statements_percent = models.IntegerField(null=True, blank=True)
    test_mobile_apex_push_used = models.IntegerField(null=True, blank=True)
    test_mobile_apex_push_allowed = models.IntegerField(null=True, blank=True)
    test_mobile_apex_push_percent = models.IntegerField(null=True, blank=True)
    test_heap_size_used = models.IntegerField(null=True, blank=True)
    test_heap_size_allowed = models.IntegerField(null=True, blank=True)
    test_heap_size_percent = models.IntegerField(null=True, blank=True)
    test_sosl_queries_used = models.IntegerField(null=True, blank=True)
    test_sosl_queries_allowed = models.IntegerField(null=True, blank=True)
    test_sosl_queries_percent = models.IntegerField(null=True, blank=True)
    test_queueable_jobs_used = models.IntegerField(null=True, blank=True)
    test_queueable_jobs_allowed = models.IntegerField(null=True, blank=True)
    test_queueable_jobs_percent = models.IntegerField(null=True, blank=True)
    test_callouts_used = models.IntegerField(null=True, blank=True)
    test_callouts_allowed = models.IntegerField(null=True, blank=True)
    test_callouts_percent = models.IntegerField(null=True, blank=True)
    worst_limit = models.CharField(max_length=255, null=True, blank=True)
    worst_limit_percent = models.IntegerField(null=True, blank=True, db_index=True)
    worst_limit_nontest = models.CharField(max_length=255, null=True, blank=True)
    worst_limit_nontest_percent = models.IntegerField(null=True, blank=True)
    worst_limit_test = models.CharField(max_length=255, null=True, blank=True)
    worst_limit_test_percent = models.IntegerField(null=True, blank=True)

    objects = TestResultManager()

    class Meta:
        verbose_name = "Test Result"
        verbose_name_plural = "Test Results"

    def __str__(self):
        return "%s.%s" % (self.method.testclass, self.method.name)

    def get_absolute_url(self):
        return reverse("test_result_detail", kwargs={"result_id": str(self.id)})

    def get_robot_url(self):
        return reverse("test_result_robot", kwargs={"result_id": str(self.id)})

    def get_limit_types(self):
        types = (
            "email_invocations",
            "soql_queries",
            "future_calls",
            "dml_rows",
            "cpu_time",
            "query_rows",
            "dml_statements",
            "mobile_apex_push",
            "heap_size",
            "sosl_queries",
            "queueable_jobs",
            "callouts",
        )

        return types


def asset_upload_to(instance, filename):
    folder = instance.result.build_flow.asset_hash
    return os.path.join(folder, filename)


class TestResultAsset(models.Model):
    result = models.ForeignKey(
        TestResult, related_name="assets", on_delete=models.CASCADE
    )
    asset = models.FileField(upload_to=asset_upload_to)

    # pytest: This is not a test
    __test__ = False


FieldType = namedtuple("FieldType", ["label", "aggregation"])


class Percentile(Aggregate):
    function = "PERCENTILE_CONT"
    name = "percentile"
    output_field = FloatField()
    template = "%(function)s(%(percentile)s) WITHIN GROUP (ORDER BY %(expressions)s)"
    allow_distinct = False


def NearMin(field):
    "DB Statistical function for almost the minimum but not quite."
    return Percentile(field, percentile=0.05)


def NearMax(field):
    "DB Statistical function for almost the maximum but not quite."
    return Percentile(field, percentile=0.95)


class TestResultPerfSummaryBase(models.Model):
    """Abstract base class mode which can be used to summarize by different
    time periods e.g. daily, weekly, monthly. Currently used only
    by a weekly base class"""

    class Meta:
        abstract = True

    rel_repo = models.ForeignKey(
        "repository.Repository",
        #        related_name="testresult_perfsummaries",
        db_column="repo_id",
        on_delete=models.CASCADE,
    )
    rel_branch = models.ForeignKey(
        "repository.Branch",
        #        related_name="testresult_perfsummaries",
        null=False,
        blank=False,
        db_column="branch_id",
        on_delete=models.CASCADE,
    )

    rel_plan = models.ForeignKey(
        "plan.Plan",
        #        related_name="testresult_perfsummaries",
        null=False,
        blank=False,
        db_column="plan_id",
        on_delete=models.CASCADE,
    )

    rel_planrepo = models.ForeignKey(
        "plan.PlanRepository",
        null=False,
        blank=False,
        db_column="planrepo_id",
        on_delete=models.CASCADE,
    )

    method = models.ForeignKey(
        TestMethod,
        #        related_name="testresult_perfsummaries",
        null=False,
        blank=False,
        on_delete=models.CASCADE,
    )

    agg_duration_average = models.FloatField(null=True, blank=False)
    agg_duration_slow = models.FloatField(null=True, blank=False)
    agg_duration_fast = models.FloatField(null=True, blank=False)
    agg_cpu_usage_average = models.FloatField(null=True, blank=False)
    agg_cpu_usage_low = models.FloatField(null=True, blank=False)
    agg_cpu_usage_high = models.FloatField(null=True, blank=False)

    agg_count = models.IntegerField(null=False, blank=False)

    agg_failures = models.IntegerField(null=False, blank=False)

    agg_assertion_failures = models.IntegerField(null=False, blank=False)

    agg_DML_failures = models.IntegerField(null=False, blank=False)
    agg_other_failures = models.IntegerField(null=False, blank=False)

    metric_definitions = {
        "duration_average": FieldType("Duration: Average", Avg("duration")),
        "duration_slow": FieldType("Duration: Slow", NearMax("duration")),
        "duration_fast": FieldType("Duration: Fast", NearMin("duration")),
        "duration_stddev": FieldType("Duration: Stddev", StdDev("duration")),
        "duration_coefficient_var": FieldType(
            "Duration: VarCoef", StdDev("duration") / Avg("duration")
        ),
        "cpu_usage_average": FieldType("CPU Usage: Average", Avg("test_cpu_time_used")),
        "cpu_usage_low": FieldType("CPU Usage: Low", NearMin("test_cpu_time_used")),
        "cpu_usage_high": FieldType("CPU Usage: High", NearMax("test_cpu_time_used")),
        "count": FieldType("Count", Count("id")),
        "failures": FieldType("Failures", Count("id", filter=Q(outcome="Fail"))),
        "assertion_failures": FieldType(
            "Assertion Failures",
            Count("id", filter=Q(message__startswith="System.AssertException")),
        ),
        "DML_failures": FieldType(
            "DML Failures",
            Count("id", filter=Q(message__startswith="System.DmlException")),
        ),
        "other_failures": FieldType(
            "Other Failures",
            Count(
                "id",
                filter=Q(outcome="Fail")
                & ~Q(message__startswith="System.DmlException")
                & ~Q(message__startswith="System.AssertException"),
            ),
        ),
        "success_percentage": FieldType(
            "Success Percentage",
            Cast(Count("id", filter=Q(outcome="Pass")), FloatField())
            / Cast(Count("id"), FloatField())
            * 100,
        ),
    }

    @classmethod
    def metrics(cls):
        """Summarize the metrics to {name: calculation} (no displayName)"""
        return {name: f.aggregation for (name, f) in cls.metric_definitions.items()}

    @classmethod
    def _get_queryset_for_dates(cls, start_date, end_date, **values):
        """Get a queryset for a range of dates."""
        metrics = cls.metrics()

        buildflows = build_models.BuildFlow.objects.filter(
            time_end__date__gte=start_date, time_end__date__lte=end_date
        )

        method_contexts = (
            TestResult.objects.filter(
                build_flow_id__in=buildflows,
                build_flow__build__planrepo_id__isnull=False,
            )
            .values(
                "method_id",
                rel_repo_id=F("build_flow__build__repo"),
                rel_branch_id=F("build_flow__build__branch"),
                rel_plan_id=F("build_flow__build__plan"),
                rel_planrepo_id=F("build_flow__build__planrepo"),
                **values,
            )
            .annotate(
                agg_count=Count("method__name"),
                agg_duration_average=metrics["duration_average"],
                agg_duration_slow=metrics["duration_slow"],
                agg_duration_fast=metrics["duration_fast"],
                agg_cpu_usage_average=metrics["cpu_usage_average"],
                agg_cpu_usage_low=metrics["cpu_usage_low"],
                agg_cpu_usage_high=metrics["cpu_usage_high"],
                agg_failures=metrics["failures"],
                agg_assertion_failures=metrics["assertion_failures"],
                agg_DML_failures=metrics["DML_failures"],
                agg_other_failures=metrics["other_failures"],
            )
        )
        return method_contexts


class TestResultPerfWeeklySummaryQuerySet(models.QuerySet):
    def for_user(self, user, perms=None):
        if user.is_superuser:
            return self
        if perms is None:
            perms = "plan.view_builds"
        PlanRepository = apps.get_model("plan.PlanRepository")
        return self.filter(
            rel_planrepo__in=PlanRepository.objects.for_user(user, perms)
        )


class TestResultPerfWeeklySummary(TestResultPerfSummaryBase):
    """Weekly summary table/model"""

    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)

    class Meta:
        verbose_name = "Test Results Weekly Performance Summary"
        verbose_name_plural = "Test Results Weekly Performance Summaries"
        db_table = "testresult_weekly_perfsummary"
        unique_together = ("rel_repo", "rel_branch", "rel_plan", "method", "week_start")
        indexes = [
            models.Index(fields=unique_together, name="testresult_weekly_lookup")
        ]

    week_start = models.DateField(null=False, blank=False)
    objects = TestResultPerfWeeklySummaryQuerySet.as_manager()

    @classmethod
    def _parse_start_and_date_dates(cls, start_string, end_string):
        """This code can be called from command lines, periodic jobs or
        other code. This function provides helpful default behaviours
        and date parsing to all of those contexts."""
        from metaci.build.models import BuildFlow

        DATE_FORMAT = "%Y-%m-%d"
        if start_string:  # User supplied start
            start = datetime.datetime.strptime(start_string, DATE_FORMAT)
            start = start.replace(tzinfo=gettz()).date()
        else:
            # Infer a start date. Let's see where we left off last time.
            last_already_created = cls.objects.order_by("week_start").last()
            if last_already_created:
                start = last_already_created.week_start
                # Let's always do at least one week in case it was incomplete
                # (the week may not have been finished when we ran the scripts)
                start = start - timezone.timedelta(days=1)

            else:  # Starting from scratch
                first_buildflow = (
                    BuildFlow.objects.filter(time_end__isnull=False)
                    .order_by("time_end")
                    .first()
                )
                if first_buildflow:
                    start = first_buildflow.time_end.date()
                else:
                    return None, None  # nothing to do if buildflows table is empty!

        if end_string:
            end = datetime.datetime.strptime(end_string, DATE_FORMAT)
            end = end.replace(tzinfo=gettz()).date()
        else:
            end = (
                BuildFlow.objects.filter(time_end__isnull=False)
                .order_by("-time_end")
                .first()
                .time_end.date()
            )
        return start, end

    @classmethod
    def date_range(cls, start_date, end_date):
        """Generate a list of weeks described by two YYYY-MM-DD strings"""
        start, end = cls._parse_start_and_date_dates(start_date, end_date)

        # Turns out there is nothing to summarize
        if not start:
            return []

        # start weeks on Sunday
        start = cls._get_sunday(start)

        dates_generator = (
            start + datetime.timedelta(days=x)
            for x in range(0, (end - start).days + 1, 7)
        )

        return dates_generator

    @classmethod
    def _get_sunday(cls, day):
        """Go backwards to find the previous Sunday"""
        day_of_week = (day.weekday() + 1) % 7  # Sunday is 0, Monday is 1, etc.
        to_subtract = datetime.timedelta(days=day_of_week)
        sunday_of_week = day - to_subtract
        return sunday_of_week

    @classmethod
    def summarize_week(cls, date):
        """Build summarize rows for a week containing a date"""
        assert date
        if not hasattr(date, "weekday"):
            date = datetime.datetime.strptime(date, "%Y-%m-%d")

        week_start = cls._get_sunday(date)
        week_start_with_timezone = timezone.template_localtime(week_start, use_tz=True)
        week_end_with_timezone = timezone.template_localtime(
            week_start + timezone.timedelta(days=7), use_tz=True
        )

        method_contexts = cls._get_queryset_for_dates(
            week_start_with_timezone,
            week_end_with_timezone,
            week_start=Value(week_start, output_field=models.DateField()),
        )

        # If a week was only partially processed then we need
        # to process it again from the beginning incorporating new data.
        # So let's get rid of the old summary files.
        obsolete_objects = cls.objects.filter(week_start=week_start)
        deleted = obsolete_objects.delete()
        cls.logger.info("Deleted TestResultSummary Data %s", deleted)

        for batch in split_seq(method_contexts, 5000):
            new_objects = [cls(**values) for values in batch]
            cls.logger.info("Creating %s for %s", len(new_objects), date)
            created = cls.objects.bulk_create(new_objects)
            cls.logger.info("Created %s for %s", len(created), date)

    @classmethod
    def summarize_weeks(cls, startdate_string=None, enddate_string=None):
        """Summarize all of the weeks in a range."""
        cls.logger.info("Summarization starting")
        for date in cls.date_range(startdate_string, enddate_string):
            cls.summarize_week(date)
            cls.logger.info("Summarized week starting %s", date)
