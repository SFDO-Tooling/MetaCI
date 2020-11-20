import json
import sys
from io import StringIO
from unittest import mock

import pytest
import responses
from django.test import TestCase
from requests.exceptions import HTTPError
from simple_salesforce.exceptions import (
    SalesforceExpiredSession,
    SalesforceMalformedRequest,
)

from metaci.build.management.commands.packaging_org_users import Command
from metaci.conftest import OrgFactory

counter = 0


def fake_query(query):
    global counter
    counter += 1
    if counter == 4:
        raise SalesforceMalformedRequest("Q", "R", "S", "T")
    elif (
        query
        == "SELECT Name, Email, UserType, IsActive, UserRole.Name, Title from User WHERE IsActive=True"
    ):
        return {
            "records": [
                {
                    "Name": "Paul",
                    "Email": "paul@p.com",
                    "UserType": "Czar",
                    "IsActive": 1,
                    "UserRole": {"Name": "Maharaja"},
                    "Title": "Dogcatcher",
                }
            ]
        }
    elif (
        query
        == "SELECT Name, NamespacePrefix FROM MetadataPackage WHERE NamespacePrefix<>''"
    ):
        return {"records": [{"Name": "MyApp", "NamespacePrefix": "MyApp"}]}

    assert 0, f"Unhandled query: {query}"


@pytest.mark.django_db
class TestPackagingOrgUsers(TestCase):
    @responses.activate
    @mock.patch("metaci.build.management.commands.packaging_org_users.JSONDataStorage")
    @mock.patch("cumulusci.core.config.OrgConfig.refresh_oauth_token")
    @mock.patch("cumulusci.core.config.OrgConfig.salesforce_client")
    def test_run_command(self, salesforce_client, refresh_oauth, JSONDataStorage):
        refresh_oauth.side_effect = [
            mock.Mock(),
            SalesforceExpiredSession("A", "B", "C", "D"),
            HTTPError("E", "F", "G"),
            mock.Mock(),
        ]
        s3_mock = mock.MagicMock()
        JSONDataStorage.return_value.open.return_value = s3_mock
        OrgFactory(name="packaging", repo__name="RepoA")
        OrgFactory(name="packaging", repo__name="RepoB")
        OrgFactory(name="packaging", repo__name="RepoC")
        OrgFactory(name="packaging", repo__name="RepoD")
        salesforce_client.query = fake_query
        json_file = StringIO("w")
        s3_mock.__enter__.return_value = json_file
        c = Command()
        OrgConfigModule = sys.modules["cumulusci.core.config.OrgConfig"]
        with mock.patch.object(OrgConfigModule, "SKIP_REFRESH", True):
            c.handle()
        assert len(JSONDataStorage.return_value.url.mock_calls) > 0
        assert json.loads(json_file.getvalue()) == {
            "orgs": [
                {
                    "repo_name": "RepoA",
                    "package_name": "MyApp",
                    "namespace": "MyApp",
                    "users": [["Paul", "paul@p.com", "Czar", "Maharaja", "Dogcatcher"]],
                },
                {
                    "repo_name": "RepoD",
                    "package_name": None,
                    "namespace": None,
                    "users": [["Paul", "paul@p.com", "Czar", "Maharaja", "Dogcatcher"]],
                },
            ],
            "errors": [
                {
                    "repo": "RepoB",
                    "error": "Expired: Expired session for A. Response content: D",
                },
                {"repo": "RepoC", "error": "Error: [Errno E] F: 'G'"},
            ],
        }
