def create_status(build):
    if not build.plan.context:
        # skip setting Github status if the context field is empty
        return

    state = None
    target_url = None
    description = None
    repo = build.repo.github_api

    if build.get_status() == "queued":
        state = "pending"
        description = "The build is queued"
    if build.get_status() == "waiting":
        state = "pending"
        description = "The build is waiting for another build to complete"
    if build.get_status() == "running":
        state = "pending"
        description = "The build is running"
    if build.get_status() == "qa":
        state = "pending"
        description = f"{build.user} is testing"
    if build.get_status() == "success":
        state = "success"
        if build.commit_status:
            description = build.commit_status
        elif build.plan.role == "qa":
            description = f"{build.qa_user} approved. See details for QA comments"
        else:
            description = "The build was successful"
    elif build.get_status() == "error":
        state = "error"
        description = "💥 An error occurred during build"
    elif build.get_status() == "fail":
        state = "failure"
        if build.plan.role == "qa":
            description = f"{build.qa_user} rejected. See details for QA comments"
        else:
            plural = build.tests_fail != 1
            description = f"⚠ ️There were {build.tests_fail} test{'s' if plural else ''} that failed this check."
            target_url = f"{build.get_external_url()}/tests"

    response = repo.create_status(
        sha=build.commit,
        state=state,
        target_url=target_url or build.get_external_url(),
        description=description,
        context=build.plan.context,
    )

    return response
