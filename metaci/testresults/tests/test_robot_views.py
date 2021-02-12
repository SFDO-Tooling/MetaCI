from pathlib import Path
from unittest import mock

import pytest
from django.test import Client, TestCase
from django.urls import reverse

from metaci.conftest import (
    BuildFactory,
    FlowTaskFactory,
    StaffSuperuserFactory,
    TestResultFactory,
    UserFactory,
)


@pytest.mark.django_db
class BaseRobotResultsTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.client = Client()
        cls.superuser = StaffSuperuserFactory()
        cls.user = UserFactory()
        cls.build = BuildFactory()

    def _get_xml(self, filename):
        """Return the contents of the named XML file

        This looks in the same folder as the test for the requested file.
        """
        xml_path = Path(__file__).parent / filename
        with xml_path.open("r") as f:
            output_xml = f.read()
        return output_xml


class TestResultRobotView(BaseRobotResultsTestCase):
    def test_result_robot_404(self):

        task = FlowTaskFactory()
        test_result = TestResultFactory(
            robot_xml=self._get_xml("robot_1.xml"), task=task
        )

        self.client.force_login(self.user)
        url = reverse("test_result_robot", kwargs={"result_id": test_result.id})
        response = self.client.get(url)
        assert response.status_code == 404, "Ordinary user was able to see results"

    @mock.patch("metaci.testresults.views.rebot")
    def test_rebot_options(self, mock_rebot):
        """Verify subset of robot options are passed to rebot

        Some robot options are used by robot to generate the report.
        This test verifies that we pass on all af the relevant options
        to the `rebot` command.
        """

        # use superuser here to avoid the hassle of setting
        # up permissions for a user
        self.client.force_login(self.superuser)

        task_options = {
            option: option
            for option in (
                "critical",
                "doc",
                "flattenkeywords",
                "logtitle",
                "metadata",
                "name",
                "noncritical",
                "removekeywords",
                "settag",
                "suitestatlevel",
                "tagdoc",
                "tagstatcombine",
                "tagstatexclude",
                "tagstatinclude",
                "tagstatlink",
            )
        }

        task = FlowTaskFactory(options={"options": task_options})
        test_result = TestResultFactory(
            robot_xml=self._get_xml("robot_1.xml"), task=task
        )

        url = reverse("test_result_robot", kwargs={"result_id": test_result.id})
        response = self.client.get(url)

        assert response.status_code == 200
        (args, kwargs) = mock_rebot.call_args
        assert set(task_options.items()).issubset(set(kwargs.items()))

    @mock.patch("metaci.testresults.views.rebot")
    def test_result_robot_no_options(self, mock_rebot):
        """Verify the test_result_robot view works even in the absense of robot options"""
        task = FlowTaskFactory(options={})
        test_result = TestResultFactory(
            robot_xml=self._get_xml("robot_1.xml"), task=task
        )

        # use superuser here to avoid the hassle of setting
        # up permissions for a user
        self.client.force_login(self.superuser)
        url = reverse("test_result_robot", kwargs={"result_id": test_result.id})
        response = self.client.get(url)

        assert response.status_code == 200
        (args, kwargs) = mock_rebot.call_args
        self.assertTupleEqual(tuple(kwargs.keys()), ("log", "output", "report"))

    def test_patched_tagstat_links(self):
        """Verify that the target attribute is in some of the links

        The generated html uses javascript functions to generate
        links.  This searches for the template used in one of those
        functions to make sure the anchor element has the target
        attribute.

        """
        task = FlowTaskFactory(
            options={
                "options": {"tagstatlink": "w-*:http://example.com?id=%1:work item"}
            }
        )
        test_result = TestResultFactory(
            robot_xml=self._get_xml("robot_1.xml"), task=task
        )
        self.client.force_login(self.superuser)
        url = reverse("test_result_robot", kwargs={"result_id": test_result.id})
        response = self.client.get(url)

        self.longMessage = False  # without this, the entire html ends up on stdout.
        expected = r'<span>[<a href="{{html $value.url}}" title="{{html $value.url}}" target="_top">'
        self.assertIn(
            expected,
            str(response.content),
            "didn't find 'target=top' attribute in generated html links",
        )
