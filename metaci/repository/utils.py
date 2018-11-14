from django.conf import settings
from github3 import login

def get_github_api(repo):
    github = login(settings.GITHUB_USERNAME, settings.GITHUB_PASSWORD)
    return github.repository(repo.owner, repo.name)

    

def create_status(build):
    if not build.plan.context:
        # skip setting Github status if the context field is empty
        return

    repo = get_github_api(build.repo)

    print build.get_status()

    if build.get_status() == 'queued':
        state = 'pending'
        description = 'The build is queued'
    if build.get_status() == 'waiting':
        state = 'pending'
        description = 'The build is waiting for another build to complete'
    if build.get_status() == 'running':
        state = 'pending'
        description = 'The build is running'
    if build.get_status() == 'qa':
        state = 'pending'
        description = '{} is testing'.format(build.user)
    if build.get_status() == 'success':
        state = 'success'
        if build.plan.role == 'qa':
            description = '{} approved. See details for QA comments'.format(build.qa_user)
        else:
            description = 'The build was successful'
    elif build.get_status() == 'error':
        state = 'error'
        description = 'An error occurred during build'
    elif build.get_status() == 'fail':
        state = 'failure'
        if build.plan.role == 'qa':
            description = '{} rejected. See details for QA comments'.format(build.qa_user)
        else:
            description = 'Tests failed'

    response = repo.create_status(
        sha=build.commit,
        state=state,
        target_url=build.get_external_url(),
        description=description,
        context=build.plan.context,
    )

    return response
