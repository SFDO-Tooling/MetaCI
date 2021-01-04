"""Test cases for /api/robot, mostly focusing on csv output"""

from unittest.mock import patch

import dateutil.parser
from django.utils import timezone
from guardian.shortcuts import assign_perm
from rest_framework.test import APIClient, APITestCase

from metaci.api.views.robot import RobotTestResultViewSet
from metaci.conftest import (
    BranchFactory,
    RepositoryFactory,
    StaffSuperuserFactory,
    TestResultFactory,
    UserFactory,
)
from metaci.testresults.models import TestResult


class TestAPIRobot(APITestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.superuser = StaffSuperuserFactory()
        cls.user = UserFactory()
        cls.client = APIClient()

        repo1 = RepositoryFactory(name="repo1")
        repo2 = RepositoryFactory(name="repo2")
        main = BranchFactory(name="main")
        feature = BranchFactory(name="feature/robot")

        # The default for queries is today's date, so we need to use that
        # when creating results
        time_end = timezone.make_aware(
            dateutil.parser.parse("01:00:00"), timezone.get_current_timezone()
        )
        cls.today = time_end.strftime("%Y-%m-%d %H:%M:%S")

        # One apex test, just to make sure it doesn't appear in any test results
        TestResultFactory(
            build_flow__time_end=time_end,
            method__testclass__test_type="Apex",
            outcome="Pass",
            duration=0.1,
        )

        # ... and several robot tests, some passing, some failing
        # oof. This is one place where I think black made the code much
        # less readable than my hand-edited version.
        for (
            repo,
            source,
            outcome,
            branch,
            test_name,
            tags,
            robot_keyword,
            message,
        ) in (
            (repo1, "file1.robot", "Pass", main, "Passing 1", None, None, None),
            (repo1, "file1.robot", "Pass", main, "Passing 2", None, None, None),
            (
                repo2,
                "file2.robot",
                "Fail",
                feature,
                "Failing 1",
                "",
                "KW1",
                "epic fail",
            ),
            (
                repo2,
                "file2.robot",
                "Fail",
                feature,
                "Failing 2",
                "",
                "KW1",
                "epic fail",
            ),
            (
                repo2,
                "file3.robot",
                "Fail",
                feature,
                "Failing 3",
                "",
                "KW2",
                "epic fail",
            ),
            (
                repo2,
                "file3.robot",
                "Fail",
                feature,
                "Failing 4",
                "t1,t2",
                "KW3",
                "ʃıɐɟ ɔıdǝ",
            ),
        ):
            TestResultFactory(
                method__testclass__test_type="Robot",
                build_flow__build__repo=repo,
                build_flow__build__branch=branch,
                build_flow__time_end=time_end,
                method__name=test_name,
                outcome=outcome,
                source_file=source,
                robot_keyword=robot_keyword,
                duration=0.1,
                robot_tags=tags,
                message=message,
            )

    def test_superuser_access(self):
        """Make sure the superuser can access the API"""
        self.client.force_authenticate(self.superuser)
        response = self.client.get("/api/robot/")
        assert response.status_code == 200

    def test_unauthenticated_user_access(self):
        """Make sure an unauthenticated user cannot access the API"""

        self.client.logout()
        response = self.client.get("/api/robot.json/")
        assert response.status_code == 401

    def test_authenticated_user_access(self):
        """Make sure an authenticated user can access the API"""
        self.client.force_authenticate(self.user)
        response = self.client.get("/api/robot.json/")
        assert response.status_code == 200

    def test_result_returns_only_robot_tests(self):
        """Verify the query doesn't include Apex test results"""

        self.client.force_authenticate(self.superuser)
        response = self.client.get("/api/robot.json")
        data = response.json()

        # we should get 5 robot results, ignoring the one Apex results
        assert (
            TestResult.objects.filter(method__testclass__test_type="Apex").count() > 0
        )
        assert data["count"] == 6

    def test_result_csv_format(self):
        """Verify we can get back csv results"""
        self.client.force_authenticate(self.superuser)
        response = self.client.get("/api/robot.csv")
        expected = [
            "id,outcome,date,duration,repo_name,branch_name,source_file,test_name,robot_tags,robot_keyword,message",
            f"2,Pass,{self.today},0.1,repo1,main,file1.robot,Passing 1,,,",
            f"3,Pass,{self.today},0.1,repo1,main,file1.robot,Passing 2,,,",
            f"4,Fail,{self.today},0.1,repo2,feature/robot,file2.robot,Failing 1,,KW1,epic fail",
            f"5,Fail,{self.today},0.1,repo2,feature/robot,file2.robot,Failing 2,,KW1,epic fail",
            f"6,Fail,{self.today},0.1,repo2,feature/robot,file3.robot,Failing 3,,KW2,epic fail",
            f'7,Fail,{self.today},0.1,repo2,feature/robot,file3.robot,Failing 4,"t1,t2",KW3,ʃıɐɟ ɔıdǝ',
        ]
        actual = response.content.decode().splitlines()
        self.assertCountEqual(expected, actual)

    def test_repo_filter(self):
        self.client.force_authenticate(self.superuser)
        response = self.client.get("/api/robot.csv?repo_name=repo2")
        expected = [
            "id,outcome,date,duration,repo_name,branch_name,source_file,test_name,robot_tags,robot_keyword,message",
            f"4,Fail,{self.today},0.1,repo2,feature/robot,file2.robot,Failing 1,,KW1,epic fail",
            f"5,Fail,{self.today},0.1,repo2,feature/robot,file2.robot,Failing 2,,KW1,epic fail",
            f"6,Fail,{self.today},0.1,repo2,feature/robot,file3.robot,Failing 3,,KW2,epic fail",
            f'7,Fail,{self.today},0.1,repo2,feature/robot,file3.robot,Failing 4,"t1,t2",KW3,ʃıɐɟ ɔıdǝ',
        ]
        actual = response.content.decode().splitlines()
        self.assertCountEqual(expected, actual)

    def test_branch_filter(self):
        self.client.force_authenticate(self.superuser)
        response = self.client.get("/api/robot.csv?branch_name=main")
        expected = [
            "id,outcome,date,duration,repo_name,branch_name,source_file,test_name,robot_tags,robot_keyword,message",
            f"2,Pass,{self.today},0.1,repo1,main,file1.robot,Passing 1,,,",
            f"3,Pass,{self.today},0.1,repo1,main,file1.robot,Passing 2,,,",
        ]
        actual = response.content.decode().splitlines()
        self.assertCountEqual(expected, actual)

    def test_outcome_filter(self):
        self.client.force_authenticate(self.superuser)
        response = self.client.get("/api/robot.csv?outcome=Fail")
        expected = [
            "id,outcome,date,duration,repo_name,branch_name,source_file,test_name,robot_tags,robot_keyword,message",
            f"4,Fail,{self.today},0.1,repo2,feature/robot,file2.robot,Failing 1,,KW1,epic fail",
            f"5,Fail,{self.today},0.1,repo2,feature/robot,file2.robot,Failing 2,,KW1,epic fail",
            f"6,Fail,{self.today},0.1,repo2,feature/robot,file3.robot,Failing 3,,KW2,epic fail",
            f'7,Fail,{self.today},0.1,repo2,feature/robot,file3.robot,Failing 4,"t1,t2",KW3,ʃıɐɟ ɔıdǝ',
        ]
        actual = response.content.decode().splitlines()
        self.assertCountEqual(expected, actual)

    def test_test_name_filter(self):
        self.client.force_authenticate(self.superuser)
        response = self.client.get("/api/robot.csv?test_name=Failing 2")
        expected = [
            "id,outcome,date,duration,repo_name,branch_name,source_file,test_name,robot_tags,robot_keyword,message",
            f"5,Fail,{self.today},0.1,repo2,feature/robot,file2.robot,Failing 2,,KW1,epic fail",
        ]
        actual = response.content.decode().splitlines()
        self.assertCountEqual(expected, actual)

    def test_source_file_filter(self):
        self.client.force_authenticate(self.superuser)
        response = self.client.get("/api/robot.csv?source_file=file3.robot")
        expected = [
            "id,outcome,date,duration,repo_name,branch_name,source_file,test_name,robot_tags,robot_keyword,message",
            f"6,Fail,{self.today},0.1,repo2,feature/robot,file3.robot,Failing 3,,KW2,epic fail",
            f'7,Fail,{self.today},0.1,repo2,feature/robot,file3.robot,Failing 4,"t1,t2",KW3,ʃıɐɟ ɔıdǝ',
        ]
        actual = response.content.decode().splitlines()
        self.assertCountEqual(expected, actual)


class TestAPIRobotDateHandling(APITestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.superuser = StaffSuperuserFactory()
        cls.user = UserFactory()
        cls.client = APIClient()

        repo = RepositoryFactory(name="repo1")
        main = BranchFactory(name="main")

        today = timezone.make_aware(
            dateutil.parser.parse("01:00:00"), timezone.get_current_timezone()
        )
        cls.today = today.strftime("%Y-%m-%d %H:%M:%S")

        # create some data that spans several days, plus one for today
        tz = timezone.get_current_timezone()
        for date in (
            cls.today,
            "2020-Jan-01",
            "2020-Jan-02",
            "2020-Jan-02",
            "2020-Jan-03",
            "2020-Jan-03",
            "2020-Jan-03",
        ):
            time_end = timezone.make_aware(
                dateutil.parser.parse(f"{date} 01:00:00"), tz
            )
            TestResultFactory(
                method__testclass__test_type="Robot",
                build_flow__build__repo=repo,
                build_flow__build__branch=main,
                build_flow__time_end=time_end,
                method__name="Test 1",
                outcome="Pass",
                source_file="/tmp/example.robot",
                robot_keyword="Some keyword",
                robot_tags="",
                duration=0.1,
                message="",
            )

    def test_date_defaults_to_today(self):
        """Verify that by default we only return tests from today"""
        self.client.force_authenticate(self.superuser)
        response = self.client.get("/api/robot.csv")
        actual = response.content.decode().splitlines()
        expected = [
            "id,outcome,date,duration,repo_name,branch_name,source_file,test_name,robot_tags,robot_keyword,message",
            f"8,Pass,{self.today},0.1,repo1,main,/tmp/example.robot,Test 1,,Some keyword,",
        ]
        self.assertCountEqual(expected, actual)

    def test_date_from_without_to(self):
        """Verify leaving off the "to" parameter defaults to the start date"""
        self.client.force_authenticate(self.superuser)
        response = self.client.get("/api/robot.csv?from=2020-01-02")
        actual = response.content.decode().splitlines()
        expected = [
            "id,outcome,date,duration,repo_name,branch_name,source_file,test_name,robot_tags,robot_keyword,message",
            "10,Pass,2020-01-02 01:00:00,0.1,repo1,main,/tmp/example.robot,Test 1,,Some keyword,",
            "11,Pass,2020-01-02 01:00:00,0.1,repo1,main,/tmp/example.robot,Test 1,,Some keyword,",
        ]
        self.assertCountEqual(expected, actual)

    def test_date_from_to(self):
        """Verify that results are returned between two dates"""
        self.client.force_authenticate(self.superuser)
        response = self.client.get("/api/robot.csv?from=2020-01-02&to=2020-01-03")
        actual = response.content.decode().splitlines()
        expected = [
            "id,outcome,date,duration,repo_name,branch_name,source_file,test_name,robot_tags,robot_keyword,message",
            "10,Pass,2020-01-02 01:00:00,0.1,repo1,main,/tmp/example.robot,Test 1,,Some keyword,",
            "11,Pass,2020-01-02 01:00:00,0.1,repo1,main,/tmp/example.robot,Test 1,,Some keyword,",
            "12,Pass,2020-01-03 01:00:00,0.1,repo1,main,/tmp/example.robot,Test 1,,Some keyword,",
            "13,Pass,2020-01-03 01:00:00,0.1,repo1,main,/tmp/example.robot,Test 1,,Some keyword,",
            "14,Pass,2020-01-03 01:00:00,0.1,repo1,main,/tmp/example.robot,Test 1,,Some keyword,",
        ]
        self.assertCountEqual(expected, actual)


class TestAPIRobotTimePeriods(APITestCase):
    """Verify the date range computations are correct"""

    def test_range(self):

        errors = []
        with patch(
            "metaci.api.views.robot.RobotTestResultViewSet._get_today"
        ) as mock_get_today:
            # Note: Monday of the week with this date is Dec 30,
            # chosen to handle the case of last week, last month cross
            # month and year boundaries
            mock_get_today.return_value = dateutil.parser.parse("2020-01-01").date()

            ranges = {
                "today": ("2020-01-01", "2020-01-02"),
                "yesterday": ("2019-12-31", "2020-01-01"),
                "thisweek": ("2019-12-30", "2020-01-02"),
                "lastweek": ("2019-12-23", "2019-12-30"),
                "thismonth": ("2020-01-01", "2020-02-01"),
                "lastmonth": ("2019-12-01", "2020-01-01"),
            }
            viewset = RobotTestResultViewSet()
            for range_name, expected_ranges in ranges.items():
                actual_start, actual_end = viewset._get_date_range(range_name)
                expected_start, expected_end = (
                    dateutil.parser.parse(date).date() for date in expected_ranges
                )
                if expected_start != actual_start:
                    errors.append(
                        f"{range_name}: start expected {expected_start} actual {actual_start}"
                    )
                if expected_end != actual_end:
                    errors.append(
                        f"{range_name}: end expected {expected_end} actual {actual_end}"
                    )
        assert not errors, "date range exceptions\n" + "\n".join(errors)


class TestAPIRobotFilterByUser(APITestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.superuser = StaffSuperuserFactory()
        cls.user = UserFactory()
        cls.client = APIClient()

        TestResultFactory(method__testclass__test_type="Robot")
        TestResultFactory(method__testclass__test_type="Robot")
        TestResultFactory(method__testclass__test_type="Robot")

        testresults = TestResult.objects.all()
        assign_perm(
            "plan.view_builds", cls.user, testresults[0].build_flow.build.planrepo
        )
        assign_perm(
            "plan.view_builds", cls.user, testresults[1].build_flow.build.planrepo
        )

    def test_testresult_filter__as_user(self):
        """Verify user only sees the results they are allowed to see"""
        self.client.force_authenticate(self.user)
        response = self.client.get("/api/robot.json")
        data = response.json()
        assert data["count"] == 2

    def test_testresult_filter__as_superuser(self):
        """Verify superuser sees all results"""
        self.client.force_authenticate(self.superuser)
        response = self.client.get("/api/robot.json")
        data = response.json()
        assert data["count"] == 3
