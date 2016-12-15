from django.conf import settings
from github3 import login


def create_status(build, state):
    github = login(settings.GITHUB_USERNAME, settings.GITHUB_PASSWORD)
    repo = github.repository(build.repo.owner, build.repo.name)
    repo.create_status(
        sha=build.commit,
        state=state,
        target_url=build.get_absolute_url(),
        context=build.trigger.context,
    )
