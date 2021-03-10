import os

from cumulusci.core.github import get_github_api_for_repo
from cumulusci.oauth.salesforce import CaptureSalesforceOAuth
from django.conf import settings
from django.core.management.base import BaseCommand
from requests.adapters import HTTPAdapter

from metaci.build.tasks import scratch_org_limits
from metaci.cumulusci.keychain import GitHubSettingsKeychain
from metaci.cumulusci.utils import get_connected_app


class Command(BaseCommand):
    help = "Test the installation environment."

    def handle(self, *args, **options):
        successes = []
        errors = []

        tests = [
            (
                scratch_org_limits,
                "Dev Hub seems to be configured",
                "Dev Hub is not configured. Scratch org creation will fail",
            ),
            (
                test_github,
                "GitHub API is configured",
                "GitHub API is not configured. Repos cannot be retrieved for builds.",
            ),
            (
                test_connected_app,
                "Connected app environment variables allowed oauth",
                "Connected app is not configured.  Persistent org connection will fail",
            ),
            (
                test_github_webhook_setting,
                "Github Webhook Secret is set, but cannot be tested",
                "Github Webhook Secret is not set. Github actions will not be able to trigger builds.",
            ),
        ]

        for test in tests:
            func, good, bad = test
            try:
                func()
                successes.append(good)
            except BaseException as e:
                errors.append(f"{bad}: {e}")

        print("")
        print("")

        for success in successes:
            print("SUCCESS:", success)

        if errors:
            print()
            for error in errors:
                print("ERROR:", error)
            print()
            print("There were errors:")
            print("Check your .env file or environment.")
            print("Please read configuring.rst for more details.")


def test_connected_app():
    app = get_connected_app()
    assert app.client_id and isinstance(app.client_id, str)
    assert app.client_secret and isinstance(app.client_secret, str)
    assert app.callback_url and isinstance(app.callback_url, str)
    print()
    print("You can log into any org to test oauth.")
    print()

    oauth_capture = CaptureSalesforceOAuth(
        client_id=app.client_id,
        client_secret=app.client_secret,
        callback_url=app.callback_url,
        auth_site=settings.SF_PROD_LOGIN_URL,
        scope="web full refresh_token",
    )
    oauth_capture()
    print()


def test_github():
    assert (settings.GITHUB_USERNAME and settings.GITHUB_PASSWORD) or (
        os.environ.get("GITHUB_APP_ID") and os.environ("GITHUB_APP_KEY")
    )
    if settings.GITHUB_USERNAME:
        keychain = GitHubSettingsKeychain()
        print("Using GITHUB_USERNAME")
    else:
        keychain = None
        print("Using GITHUB_APP_ID")
    api = get_github_api_for_repo(keychain, "github", "docs")
    api.session.mount("https://api.github.com", HTTPAdapter(max_retries=0))
    print(api.me())


def test_github_webhook_setting():
    assert settings.GITHUB_WEBHOOK_SECRET
