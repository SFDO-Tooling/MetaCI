from django.conf import settings
from github3 import login


def create_status(build):
    if not build.plan.context:
        # skip setting Github status if the context field is empty
        return

    github = login(settings.GITHUB_USERNAME, settings.GITHUB_PASSWORD)
    repo = github.repository(build.repo.owner, build.repo.name)

    if build.status == 'queued':
        state = 'pending'
        description = 'The build is queued'
    if build.status == 'waiting':
        state = 'pending'
        description = 'The build is waiting for another build to complete'
    if build.status == 'running':
        state = 'pending'
        description = 'The build is running'
    if build.status == 'success':
        state = 'success'
        description = 'The build was successful'
    elif build.status == 'error':
        state = 'error'
        description = 'An error occurred during build'
    elif build.status == 'fail':
        state = 'failure'
        description = 'Tests failed'

    response = repo.create_status(
        sha=build.commit,
        state=state,
        target_url=build.get_external_url(),
        description=description,
        context=build.plan.context,
    )

    return response
