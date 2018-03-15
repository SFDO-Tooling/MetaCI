from django_rq import job

from metaci.repository.models import Branch


@job('short')
def prune_branches():
    for branch in Branch.objects.all():
        if not branch.github_api:
            branch.delete()
