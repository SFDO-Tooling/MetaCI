import io
import json
import sys
from unittest import mock

import pytest
import responses
from django.test import TestCase
from requests.exceptions import HTTPError
from simple_salesforce.exceptions import (
    SalesforceExpiredSession,
    SalesforceMalformedRequest,
)

from metaci.conftest import OrgFactory
from metaci.users.management.commands.packaging_org_users import Command

counter = 0


def fake_query(query):
    global counter
    counter += 1
    if counter == 4:
        raise SalesforceMalformedRequest("Q", "R", "S", "T")
    elif (
        query
        == "SELECT Name, Email, UserType, IsActive, Profile.Name, Title from User WHERE IsActive=True"
    ):
        return {
            "records": [
                {
                    "Name": "Paul",
                    "Email": "paul@p.com",
                    "UserType": "Czar",
                    "IsActive": 1,
                    "Profile": {"Name": "Maharaja"},
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
    @mock.patch("cumulusci.core.config.OrgConfig.refresh_oauth_token")
    @mock.patch("cumulusci.core.config.OrgConfig.salesforce_client")
    def test_run_command(self, salesforce_client, refresh_oauth):
        refresh_oauth.side_effect = [
            mock.Mock(),
            SalesforceExpiredSession("A", "B", "C", "D"),
            HTTPError("E", "F", "G"),
            mock.Mock(),
        ]
        OrgFactory(name="packaging", repo__name="RepoA")
        OrgFactory(name="packaging", repo__name="RepoB")
        OrgFactory(name="packaging", repo__name="RepoC")
        OrgFactory(name="packaging", repo__name="RepoD")
        salesforce_client.query = fake_query
        c = Command()
        OrgConfigModule = sys.modules["cumulusci.core.config.OrgConfig"]
        with mock.patch.object(OrgConfigModule, "SKIP_REFRESH", True):
            output = io.StringIO()
            c.handle(stream=output)
        assert json.loads(output.getvalue()) == {
            "orgs": [
                {
                    "repo_name": "RepoA",
                    "package_name": "MyApp",
                    "namespace": "MyApp",
                    "users": [
                        {
                            "Name": "Paul",
                            "Email": "paul@p.com",
                            "UserType": "Czar",
                            "Profile": "Maharaja",
                            "Title": "Dogcatcher",
                        }
                    ],
                },
                {
                    "repo_name": "RepoD",
                    "package_name": None,
                    "namespace": None,
                    "users": [
                        {
                            "Name": "Paul",
                            "Email": "paul@p.com",
                            "UserType": "Czar",
                            "Profile": "Maharaja",
                            "Title": "Dogcatcher",
                        }
                    ],
                },
            ],
            "errors": [
                {
                    "repo": "RepoB",
                    "error": "Expired: Expired session for A. Response content: D",
                },
                {"repo": "RepoC", "error": "HTTPError: [Errno E] F: 'G'"},
            ],
        }
