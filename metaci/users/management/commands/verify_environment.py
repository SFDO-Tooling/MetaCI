import os

from cumulusci.core.github import get_github_api_for_repo
from django.conf import settings
from django.core.management.base import BaseCommand
from requests.adapters import HTTPAdapter

from metaci.build.tasks import scratch_org_limits
from metaci.cumulusci.keychain import GitHubSettingsKeychain


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
