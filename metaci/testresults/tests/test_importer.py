import pytest

from metaci.testresults.importer import import_test_results, populate_limit_fields
from metaci.testresults.models import TestClass, TestMethod, TestResult


@pytest.mark.django_db
class TestImporter:
    def test_import_test_results(self, data):
        num_test_classes = TestClass.objects.all().count()
        num_test_methods = TestMethod.objects.all().count()
        num_test_results = TestResult.objects.all().count()

        with open("metaci/testresults/tests/junit_output.xml", "r") as f:
            results = data["buildflow"].load_junit(f)
        import_test_results(data["buildflow"], results, "Apex")

        assert TestClass.objects.all().count() == num_test_classes + 1
        assert TestMethod.objects.all().count() == num_test_methods + 2
        assert TestResult.objects.all().count() == num_test_results + 2

        test_result = TestResult.objects.get(method__name="test_method1")
        assert test_result.duration == 5.99
        assert test_result.outcome == "Pass"

    def test_populate_limit_fields(self, data):
        test_result = data["testresult"]
        code_unit = {
            "TESTING_LIMITS: Number of SOQL queries": {"used": 10, "allowed": 100},
            "TESTING_LIMITS: Number of DML rows": {"used": 20, "allowed": 100},
        }
        populate_limit_fields(test_result, code_unit)

        worst_limit = "test_dml_rows_percent"
        worst_limit_percent = 20.0

        assert test_result.worst_limit == worst_limit
        assert test_result.worst_limit_percent == worst_limit_percent
        assert test_result.worst_limit_test == worst_limit
        assert test_result.worst_limit_test_percent == worst_limit_percent
