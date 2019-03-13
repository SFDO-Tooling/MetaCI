from __future__ import unicode_literals

import os
import dateutil.parser
from collections import OrderedDict
from django.db import models
from django import forms
from django.urls import reverse
from metaci.testresults.choices import OUTCOME_CHOICES
from metaci.testresults.choices import TEST_TYPE_CHOICES


class TestClass(models.Model):
    __test__ = False  # Tell pytest that this is not a test.
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


class TestMethod(models.Model):
    __test__ = False  # Not a unit test
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


class TestResultManager(models.Manager):
    __test__ = False  # Not a unit test

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

                if not cls in results:
                    results[cls] = OrderedDict()

                if not method in results[cls]:
                    results[cls][method] = {}

                for limit in result.get_limit_types():
                    test_limit = "test_{}_used".format(limit)

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
                        if not cls in diff:
                            diff[cls] = OrderedDict()

                        if not method in diff[cls]:
                            diff[cls][method] = {}

                        if limit not in diff[cls][method]:
                            diff[cls][method][limit] = OrderedDict()

                        diff[cls][method][limit] = build_flows

        return diff


class TestResult(models.Model):
    __test__ = False  # Tell pytest that this is not a test.
    build_flow = models.ForeignKey(
        "build.BuildFlow", related_name="test_results", on_delete=models.CASCADE
    )
    method = models.ForeignKey(
        TestMethod, related_name="test_results", on_delete=models.CASCADE
    )
    duration = models.FloatField(null=True, blank=True, db_index=True)
    outcome = models.CharField(max_length=16, choices=OUTCOME_CHOICES, db_index=True)
    stacktrace = models.TextField(null=True, blank=True)
    message = models.TextField(null=True, blank=True)
    source_file = models.CharField(max_length=255)
    robot_xml = models.TextField(null=True, blank=True)
    email_invocations_used = models.IntegerField(null=True, blank=True, db_index=True)
    email_invocations_allowed = models.IntegerField(
        null=True, blank=True, db_index=True
    )
    email_invocations_percent = models.IntegerField(
        null=True, blank=True, db_index=True
    )
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
    worst_limit = models.CharField(max_length=255, null=True, blank=True, db_index=True)
    worst_limit_percent = models.IntegerField(null=True, blank=True, db_index=True)
    worst_limit_nontest = models.CharField(
        max_length=255, null=True, blank=True, db_index=True
    )
    worst_limit_nontest_percent = models.IntegerField(
        null=True, blank=True, db_index=True
    )
    worst_limit_test = models.CharField(
        max_length=255, null=True, blank=True, db_index=True
    )
    worst_limit_test_percent = models.IntegerField(null=True, blank=True, db_index=True)

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
    __test__ = False  # Tell pytest that this is not a test.
    result = models.ForeignKey(
        TestResult, related_name="assets", on_delete=models.CASCADE
    )
    asset = models.FileField(upload_to=asset_upload_to)
