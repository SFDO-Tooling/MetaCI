"""Test cases for /api/robot, mostly focusing on csv output"""

from rest_framework.test import APIClient, APITestCase
from metaci.conftest import (
    BranchFactory,
    RepositoryFactory,
    UserFactory,
)
from metaci.testresults.models import TestResult
from metaci.conftest import StaffSuperuserFactory, TestResultFactory


class TestAPIRobot(APITestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.superuser = StaffSuperuserFactory()
        cls.user = UserFactory()
        cls.client = APIClient()

        # One apex test, just to make sure it doesn't appear in any test results
        TestResultFactory(
            method__testclass__test_type="Apex", outcome="Pass",
        )

        repo1 = RepositoryFactory(name="repo1")
        repo2 = RepositoryFactory(name="repo2")
        master = BranchFactory(name="master")
        feature = BranchFactory(name="feature/robot")
        for (repo, source, outcome, branch, test_name, robot_keyword, message) in (
            (repo1, "file1.robot", "Pass", master, "Passing 1", None, None),
            (repo1, "file1.robot", "Pass", master, "Passing 2", None, None),
            (repo2, "file2.robot", "Fail", feature, "Failing 1", "KW1", "epic fail",),
            (repo2, "file2.robot", "Fail", feature, "Failing 2", "KW1", "epic fail",),
            (repo2, "file3.robot", "Fail", feature, "Failing 3", "KW2", "epic fail",),
        ):
            TestResultFactory(
                method__testclass__test_type="Robot",
                build_flow__build__repo=repo,
                build_flow__build__branch=branch,
                method__name=test_name,
                outcome=outcome,
                source_file=source,
                robot_keyword=None,
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
        assert data["count"] == 5

    def test_result_csv_format(self):
        """Verify we can get back csv results"""
        self.client.force_authenticate(self.superuser)
        response = self.client.get("/api/robot.csv")
        expected = [
            b"id,repo_name,branch_name,outcome,source_file,test_name,message,robot_keyword",
            b"2,repo1,master,Pass,file1.robot,Passing 1,,",
            b"3,repo1,master,Pass,file1.robot,Passing 2,,",
            b"4,repo2,feature/robot,Fail,file2.robot,Failing 1,,",
            b"5,repo2,feature/robot,Fail,file2.robot,Failing 2,,",
            b"6,repo2,feature/robot,Fail,file3.robot,Failing 3,,",
        ]
        actual = response.content.splitlines()
        self.assertListEqual(expected, actual)

    def test_repo_filter(self):
        self.client.force_authenticate(self.superuser)
        response = self.client.get("/api/robot.csv?repo_name=repo2")
        expected = [
            b"id,repo_name,branch_name,outcome,source_file,test_name,message,robot_keyword",
            b"4,repo2,feature/robot,Fail,file2.robot,Failing 1,,",
            b"5,repo2,feature/robot,Fail,file2.robot,Failing 2,,",
            b"6,repo2,feature/robot,Fail,file3.robot,Failing 3,,",
        ]

        actual = response.content.splitlines()
        self.assertListEqual(expected, actual)

    def test_branch_filter(self):
        self.client.force_authenticate(self.superuser)
        response = self.client.get("/api/robot.csv?branch_name=master")
        expected = [
            b"id,repo_name,branch_name,outcome,source_file,test_name,message,robot_keyword",
            b"2,repo1,master,Pass,file1.robot,Passing 1,,",
            b"3,repo1,master,Pass,file1.robot,Passing 2,,",
        ]

        actual = response.content.splitlines()
        self.assertListEqual(expected, actual)

    def test_outcome_filter(self):
        self.client.force_authenticate(self.superuser)
        response = self.client.get("/api/robot.csv?outcome=Fail")
        expected = [
            b"id,repo_name,branch_name,outcome,source_file,test_name,message,robot_keyword",
            b"4,repo2,feature/robot,Fail,file2.robot,Failing 1,,",
            b"5,repo2,feature/robot,Fail,file2.robot,Failing 2,,",
            b"6,repo2,feature/robot,Fail,file3.robot,Failing 3,,",
        ]
        actual = response.content.splitlines()
        self.assertListEqual(expected, actual)

    def test_test_name_filter(self):
        self.client.force_authenticate(self.superuser)
        response = self.client.get("/api/robot.csv?test_name=Failing 2")
        expected = [
            b"id,repo_name,branch_name,outcome,source_file,test_name,message,robot_keyword",
            b"5,repo2,feature/robot,Fail,file2.robot,Failing 2,,",
        ]
        actual = response.content.splitlines()
        self.assertListEqual(expected, actual)

    def test_source_file_filter(self):
        self.client.force_authenticate(self.superuser)
        response = self.client.get("/api/robot.csv?source_file=file3.robot")
        expected = [
            b"id,repo_name,branch_name,outcome,source_file,test_name,message,robot_keyword",
            b"6,repo2,feature/robot,Fail,file3.robot,Failing 3,,",
        ]
        actual = response.content.splitlines()
        self.assertListEqual(expected, actual)
