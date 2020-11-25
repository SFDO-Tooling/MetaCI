from metaci.build.exceptions import BuildError


def create_status(build):
    if not build.plan.context:
        # skip setting Github status if the context field is empty
        return

    state = None
    target_url = None
    description = None
    repo = build.repo.get_github_api()

    if build.get_status() == "queued":
        state = "pending"
        description = "The build is queued"

    elif build.get_status() == "waiting":
        state = "pending"
        description = "The build is waiting for another build to complete"

    elif build.get_status() == "running":
        state = "pending"
        description = "The build is running"

    elif build.get_status() == "qa":
        state = "pending"
        description = f"{build.user} is testing"

    elif build.get_status() == "success":
        state = "success"
        if build.commit_status:
            description = build.commit_status
        elif build.plan.role == "qa":
            description = f"{build.qa_user} approved. See details for QA comments"
        else:
            description = "The build was successful"

    elif build.get_status() == "error":
        state = "error"
        description = "💥  An error occurred during the build"

    elif build.get_status() == "fail":
        state = "failure"
        if build.plan.role == "qa":
            description = f"{build.qa_user} rejected. See details for QA comments"
        else:
            plural = build.tests_fail != 1
            description = f"⚠ ️There {'were' if plural else 'was'} {build.tests_fail} test{'s' if plural else ''} that failed."
            target_url = f"{build.get_external_url()}/tests"

    else:
        raise BuildError(
            f"ERROR: Unrecognized build status encountered: {build.get_status()}"
        )

    response = repo.create_status(
        sha=build.commit,
        state=state,
        target_url=target_url or build.get_external_url(),
        description=description,
        context=build.plan.context,
    )

    return response
