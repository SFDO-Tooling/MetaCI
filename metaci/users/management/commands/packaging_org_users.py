import json
import sys

from django.core.management.base import BaseCommand
from simple_salesforce.exceptions import (
    SalesforceExpiredSession,
    SalesforceMalformedRequest,
)

from metaci.cumulusci.models import Org


class Command(BaseCommand):
    help = "Creates a JSON file with user information and prints out the URL"

    def handle(
        self,
        *args,
        stream=sys.stdout,
        **options,
    ):
        packaging_orgs = Org.objects.filter(name="packaging").order_by("repo__name")
        orgdata = [_handle_packaging_org(org) for org in packaging_orgs]
        good_orgs = [org for org in orgdata if org.get("users")]
        bad_orgs = [org for org in orgdata if org.get("error")]
        assert len(good_orgs) + len(bad_orgs) == len(orgdata)
        data = {
            "orgs": good_orgs,
            "errors": bad_orgs,
        }
        json.dump(data, stream, indent=1)


def _handle_packaging_org(org):
    print("Packaging org for", org.repo.name, file=sys.stderr)
    org_config = org.get_org_config()
    try:
        org_config.refresh_oauth_token(keychain=None)
        sf = org_config.salesforce_client
        users = sf.query(
            "SELECT Name, Email, UserType, IsActive, Profile.Name, Title from User WHERE IsActive=True"
        )
        name, namespace = None, None
        try:
            packages = sf.query(
                "SELECT Name, NamespacePrefix FROM MetadataPackage WHERE NamespacePrefix<>''"
            )["records"]
            assert len(packages) == 1
            first_package = packages[0]
            name, namespace = first_package["Name"], first_package["NamespacePrefix"]
        except SalesforceMalformedRequest:
            pass
        return {
            "repo_name": org.repo.name,
            "package_name": name,
            "namespace": namespace,
            "users": [
                {
                    "Name": user["Name"],
                    "Email": user["Email"],
                    "UserType": user["UserType"],
                    "Profile": user["Profile"]["Name"] if user["Profile"] else None,
                    "Title": user["Title"],
                }
                for user in users["records"]
            ],
        }
    except SalesforceExpiredSession as e:
        print(f"Expired: {e}", file=sys.stderr)
        return {"repo": org.repo.name, "error": f"Expired: {e}"}
    except Exception as e:
        print(f"{type(e).__name__}: {e}", file=sys.stderr)
        return {"repo": org.repo.name, "error": f"{type(e).__name__}: {e}"}
