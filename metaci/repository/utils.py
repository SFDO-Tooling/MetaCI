from metaci.build.exceptions import BuildError


def create_status(build):
    if not build.plan.context:
        # skip setting Github status if the context field is empty
        return

    state = None
    target_url = build.get_external_url()
    description = None
    repo = build.repo.get_github_api()

    build_status = build.get_status()

    if build_status == "queued":
        state = "pending"
        description = "The build is queued"

    elif build_status == "waiting":
        state = "pending"
        description = "The build is waiting for another build to complete"

    elif build_status == "running":
        state = "pending"
        description = "The build is running"

    elif build_status == "qa":
        state = "pending"
        description = f"{build.user} is testing"

    elif build_status == "success":

        state = "success"
        if build.commit_status:
            description = build.commit_status
        elif build.plan.role == "qa":
            description = f"{build.qa_user} approved. See details for QA comments"
        else:
            description = "The build was successful"

    elif build_status == "error":
        state = "error"
        description = "An error occurred during the build"

    elif build_status == "fail":
        state = "failure"
        if build.plan.role == "qa":
            description = f"{build.qa_user} rejected. See details for QA comments"
        else:
            total_tests = 0
            failed_tests = 0
            for bf in build.flows.filter(rebuild=build.current_rebuild):
                if bf.tests_fail:
                    failed_tests += bf.tests_fail
                if bf.tests_total:
                    total_tests += bf.tests_total

            description = f"⚠ ️{failed_tests}/{total_tests} failed"
            target_url = f"{build.get_external_url()}/tests"

    else:
        raise BuildError(f"Unrecognized build status encountered: {build_status}")

    response = repo.create_status(
        sha=build.commit,
        state=state,
        target_url=target_url,
        description=description,
        context=build.plan.context,
    )

    return response
