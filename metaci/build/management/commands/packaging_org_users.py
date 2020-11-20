import json

from django.core.management.base import BaseCommand
from requests.exceptions import HTTPError
from simple_salesforce.exceptions import (
    SalesforceExpiredSession,
    SalesforceMalformedRequest,
)
from storages.backends.s3boto3 import S3Boto3Storage

from metaci.cumulusci.models import Org

FILENAME = "user_list.json"


class JSONDataStorage(S3Boto3Storage):
    location = "jsondata"
    file_overwrite = True


class Command(BaseCommand):
    help = "Creates a JSON file with user information and prints out the URL"

    def handle(
        self,
        *args,
        **options,
    ):
        packaging_orgs = Org.objects.filter(name="packaging").order_by("repo__name")
        orgdata = [_handle_packaging_org(org) for org in packaging_orgs]
        good_orgs = [org for org in orgdata if org.get("users")]
        bad_orgs = [org for org in orgdata if org.get("error")]
        assert len(good_orgs) + len(bad_orgs) == len(orgdata)
        storage = JSONDataStorage()
        with storage.open(FILENAME, "wt") as f:
            data = {
                "orgs": good_orgs,
                "errors": bad_orgs,
            }
            json.dump(data, f, indent=1)
        url = storage.url(FILENAME)
        print("Created ", url)


def _handle_packaging_org(org):
    print("Packaging org for", org.repo.name)
    org_config = org.get_org_config()
    try:
        org_config.refresh_oauth_token(keychain=None)
        sf = org_config.salesforce_client
        users = sf.query(
            "SELECT Name, Email, UserType, IsActive, UserRole.Name, Title from User WHERE IsActive=True"
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
                (
                    user["Name"],
                    user["Email"],
                    user["UserType"],
                    user["UserRole"]["Name"] if user["UserRole"] else None,
                    user["Title"],
                )
                for user in users["records"]
            ],
        }
    except SalesforceExpiredSession as e:
        print(f"Expired: {e}")
        return {"repo": org.repo.name, "error": f"Expired: {e}"}
    except HTTPError as e:
        print(f"Error: {e}")
        return {"repo": org.repo.name, "error": f"Error: {e}"}
