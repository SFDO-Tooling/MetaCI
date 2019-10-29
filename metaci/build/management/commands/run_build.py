import os

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from metaci.build.models import Build
from metaci.build.tasks import lock_org, run_build, scratch_org_limits
from metaci.cumulusci.models import Org
from metaci.plan.models import Plan, PlanRepository
from metaci.repository.models import Branch, Repository

User = get_user_model()


class Command(BaseCommand):
    help = "Runs a build from the command line (on local computer)."

    def add_arguments(self, parser):
        parser.add_argument("repo_name", type=str)
        parser.add_argument("branch_name", type=str)
        parser.add_argument("plan_name", type=str)
        parser.add_argument("commit", type=str)
        parser.add_argument("username_or_email", type=str)

    def handle(
        self,
        repo_name,
        branch_name,
        commit,
        plan_name,
        username_or_email,
        *args,
        **options,
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
        planrepo = PlanRepository.objects.get(plan=plan, repo=repo)
        build = Build.objects.create(
            repo=repo,
            plan=plan,
            branch=branch,
            planrepo=planrepo,
            commit=commit,
            build_type="manual-command",
            user=user,
            org=Org.objects.get(name=plan.org, repo=repo),
        )
        if build.org.scratch:
            assert (
                scratch_org_limits().remaining > settings.SCRATCH_ORG_RESERVE
            ), "Not enough scratch orgs"
        else:
            status = lock_org(build.org, build.pk)

            assert status, "Could not lock org"

        dyno = os.environ["DYNO"]
        print(f"Running build {build.pk} in {dyno}")
        run_build(build.pk)
