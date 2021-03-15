from django.core.management.base import BaseCommand

from metaci.build.management.commands._utils import make_build


class Command(BaseCommand):
    help = "Enqueue a build to run on an appropriate dyno."

    def add_arguments(self, parser):
        parser.add_argument("repo_name", type=str)
        parser.add_argument("branch_name", type=str)
        parser.add_argument("plan_name", type=str)
        parser.add_argument("commit", type=str)
        parser.add_argument("username_or_email", type=str)
        parser.add_argument(
            "--no-lock",
            action="store_true",
            help="Do not lock the org. Use with extreme caution.",
        )

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
        make_build(
            repo_name,
            branch_name,
            commit,
            plan_name,
            username_or_email,
        )
