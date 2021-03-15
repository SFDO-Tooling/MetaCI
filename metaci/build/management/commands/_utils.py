import os

from django.conf import settings
from django.contrib.auth import get_user_model

from metaci.build.models import Build
from metaci.build.tasks import lock_org, run_build, scratch_org_limits
from metaci.cumulusci.models import Org
from metaci.plan.models import Plan, PlanRepository
from metaci.repository.models import Branch, Repository

User = get_user_model()


def make_build(
    repo_name,
    branch_name,
    commit,
    plan_name,
    username_or_email,
):
    repo = Repository.objects.get(name=repo_name)
    branch = Branch.objects.get(repo=repo, name=branch_name)
    plan = Plan.objects.get(name=plan_name)
    user = (
        User.objects.filter(username=username_or_email).first()
        or User.objects.filter(email=username_or_email).first()
    )
    assert user, (
        "Could not find user with username or email matching " + username_or_email
    )
    build_type = "manual-command"
    planrepo = PlanRepository.objects.get(plan=plan, repo=repo)
    build = Build.objects.create(
        repo=repo,
        plan=plan,
        branch=branch,
        planrepo=planrepo,
        commit=commit,
        build_type=build_type,
        user=user,
        org=Org.objects.get(name=plan.org, repo=repo),
    )
    build.save()
    return build


def do_build(build_id, no_lock=False):
    build = Build.objects.get(id=build_id)
    if build.org.scratch:
        assert (
            scratch_org_limits().remaining > settings.SCRATCH_ORG_RESERVE
        ), "Not enough scratch orgs"
    elif not no_lock:
        status = lock_org(build.org, build.pk, build.plan.build_timeout)

        assert status, "Could not lock org"

    dyno = os.environ.get("DYNO")
    if dyno:
        print(f"Running build {build.pk} in {dyno}")
    else:
        print(f"Running build {build.pk}")
    return run_build(build.pk)
