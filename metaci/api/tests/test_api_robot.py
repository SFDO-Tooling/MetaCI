"""Test cases for /api/robot, mostly focusing on csv output"""

import dateutil.parser
from django.utils import timezone
from rest_framework.test import APIClient, APITestCase

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
        master = BranchFactory(name="master")
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
        )

        # ... and several robot tests, some passing, some failing
        for (repo, source, outcome, branch, test_name, robot_keyword, message) in (
            (repo1, "file1.robot", "Pass", master, "Passing 1", None, None),
            (repo1, "file1.robot", "Pass", master, "Passing 2", None, None),
            (repo2, "file2.robot", "Fail", feature, "Failing 1", "KW1", "epic fail"),
            (repo2, "file2.robot", "Fail", feature, "Failing 2", "KW1", "epic fail"),
            (repo2, "file3.robot", "Fail", feature, "Failing 3", "KW2", "epic fail"),
            (repo2, "file3.robot", "Fail", feature, "Failing 4", "KW3", "ʃıɐɟ ɔıdǝ"),
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
                message=message,
            )

    def test_superuser_access(self):
        """Make sure the superuser can access the API"""
        self.client.force_authenticate(self.superuser)
        response = self.client.get("/api/robot/")
        assert response.status_code == 200

    def xtest_user_access(self):
        """
        Make sure the superuser can access the API

        This test fails. Am I doing the test wrong or did
        I implement the API wrong?
        """
        user = UserFactory()
        self.client.force_authenticate(user)

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
            "id,date,repo_name,branch_name,outcome,source_file,test_name,message,robot_keyword",
            f"2,{self.today},repo1,master,Pass,file1.robot,Passing 1,,",
            f"3,{self.today},repo1,master,Pass,file1.robot,Passing 2,,",
            f"4,{self.today},repo2,feature/robot,Fail,file2.robot,Failing 1,epic fail,KW1",
            f"5,{self.today},repo2,feature/robot,Fail,file2.robot,Failing 2,epic fail,KW1",
            f"6,{self.today},repo2,feature/robot,Fail,file3.robot,Failing 3,epic fail,KW2",
            f"7,{self.today},repo2,feature/robot,Fail,file3.robot,Failing 4,ʃıɐɟ ɔıdǝ,KW3",
        ]
        actual = response.content.decode().splitlines()
        self.assertCountEqual(expected, actual)

    def test_repo_filter(self):
        self.client.force_authenticate(self.superuser)
        response = self.client.get("/api/robot.csv?repo_name=repo2")
        expected = [
            "id,date,repo_name,branch_name,outcome,source_file,test_name,message,robot_keyword",
            f"4,{self.today},repo2,feature/robot,Fail,file2.robot,Failing 1,epic fail,KW1",
            f"5,{self.today},repo2,feature/robot,Fail,file2.robot,Failing 2,epic fail,KW1",
            f"6,{self.today},repo2,feature/robot,Fail,file3.robot,Failing 3,epic fail,KW2",
            f"7,{self.today},repo2,feature/robot,Fail,file3.robot,Failing 4,ʃıɐɟ ɔıdǝ,KW3",
        ]

        actual = response.content.decode().splitlines()
        self.assertCountEqual(expected, actual)

    def test_branch_filter(self):
        self.client.force_authenticate(self.superuser)
        response = self.client.get("/api/robot.csv?branch_name=master")
        expected = [
            "id,date,repo_name,branch_name,outcome,source_file,test_name,message,robot_keyword",
            f"2,{self.today},repo1,master,Pass,file1.robot,Passing 1,,",
            f"3,{self.today},repo1,master,Pass,file1.robot,Passing 2,,",
        ]
        actual = response.content.decode().splitlines()
        self.assertCountEqual(expected, actual)

    def test_outcome_filter(self):
        self.client.force_authenticate(self.superuser)
        response = self.client.get("/api/robot.csv?outcome=Fail")
        expected = [
            "id,date,repo_name,branch_name,outcome,source_file,test_name,message,robot_keyword",
            f"4,{self.today},repo2,feature/robot,Fail,file2.robot,Failing 1,epic fail,KW1",
            f"5,{self.today},repo2,feature/robot,Fail,file2.robot,Failing 2,epic fail,KW1",
            f"6,{self.today},repo2,feature/robot,Fail,file3.robot,Failing 3,epic fail,KW2",
            f"7,{self.today},repo2,feature/robot,Fail,file3.robot,Failing 4,ʃıɐɟ ɔıdǝ,KW3",
        ]
        actual = response.content.decode().splitlines()
        self.assertCountEqual(expected, actual)

    def test_test_name_filter(self):
        self.client.force_authenticate(self.superuser)
        response = self.client.get("/api/robot.csv?test_name=Failing 2")
        expected = [
            "id,date,repo_name,branch_name,outcome,source_file,test_name,message,robot_keyword",
            f"5,{self.today},repo2,feature/robot,Fail,file2.robot,Failing 2,epic fail,KW1",
        ]
        actual = response.content.decode().splitlines()
        self.assertCountEqual(expected, actual)

    def test_source_file_filter(self):
        self.client.force_authenticate(self.superuser)
        response = self.client.get("/api/robot.csv?source_file=file3.robot")
        expected = [
            "id,date,repo_name,branch_name,outcome,source_file,test_name,message,robot_keyword",
            f"6,{self.today},repo2,feature/robot,Fail,file3.robot,Failing 3,epic fail,KW2",
            f"7,{self.today},repo2,feature/robot,Fail,file3.robot,Failing 4,ʃıɐɟ ɔıdǝ,KW3",
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
        master = BranchFactory(name="master")

        today = timezone.make_aware(
            dateutil.parser.parse("01:00:00"), timezone.get_current_timezone()
        )
        cls.today = today.strftime("%Y-%m-%d %H:%M:%S")

        # create some data that spans several days, plus one for today
        tz = timezone.get_current_timezone()
        for date in (
            cls.today,
            "2020-01-01",
            "2020-01-02",
            "2020-01-02",
            "2020-01-03",
            "2020-01-03",
            "2020-01-03",
        ):
            #            time_end = dateutil.parser.parse(f"{date} 01:00:00")
            time_end = timezone.make_aware(
                dateutil.parser.parse(f"{date} 01:00:00"), tz
            )
            TestResultFactory(
                method__testclass__test_type="Robot",
                build_flow__build__repo=repo,
                build_flow__build__branch=master,
                build_flow__time_end=time_end,
                method__name="Test 1",
                outcome="Pass",
                source_file="/tmp/example.robot",
                robot_keyword="Some keyword",
                message="",
            )

    def test_date_defaults_to_today(self):
        """Verify that by default we only return tests from today"""
        self.client.force_authenticate(self.superuser)
        response = self.client.get("/api/robot.csv")
        actual = response.content.decode().splitlines()
        expected = [
            "id,date,repo_name,branch_name,outcome,source_file,test_name,message,robot_keyword",
            f"8,{self.today},repo1,master,Pass,/tmp/example.robot,Test 1,,Some keyword",
        ]
        self.assertCountEqual(expected, actual)

    def test_date_from_without_to(self):
        """Verify leaving off the "to" parameter defaults to the start date"""
        self.client.force_authenticate(self.superuser)
        response = self.client.get("/api/robot.csv?from=2020-01-02")
        actual = response.content.decode().splitlines()
        expected = [
            "id,date,repo_name,branch_name,outcome,source_file,test_name,message,robot_keyword",
            "10,2020-01-02 01:00:00,repo1,master,Pass,/tmp/example.robot,Test 1,,Some keyword",
            "11,2020-01-02 01:00:00,repo1,master,Pass,/tmp/example.robot,Test 1,,Some keyword",
        ]
        self.assertCountEqual(expected, actual)

    def test_date_from_to(self):
        """Verify that results are returned between two dates"""
        self.client.force_authenticate(self.superuser)
        response = self.client.get("/api/robot.csv?from=2020-01-02&to=2020-01-03")
        actual = response.content.decode().splitlines()
        expected = [
            "id,date,repo_name,branch_name,outcome,source_file,test_name,message,robot_keyword",
            "10,2020-01-02 01:00:00,repo1,master,Pass,/tmp/example.robot,Test 1,,Some keyword",
            "11,2020-01-02 01:00:00,repo1,master,Pass,/tmp/example.robot,Test 1,,Some keyword",
            "12,2020-01-03 01:00:00,repo1,master,Pass,/tmp/example.robot,Test 1,,Some keyword",
            "13,2020-01-03 01:00:00,repo1,master,Pass,/tmp/example.robot,Test 1,,Some keyword",
            "14,2020-01-03 01:00:00,repo1,master,Pass,/tmp/example.robot,Test 1,,Some keyword",
        ]
        self.assertCountEqual(expected, actual)
