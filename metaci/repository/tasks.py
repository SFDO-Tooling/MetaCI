from django import db
from django_rq import job

from metaci.repository.models import Branch


@job("short")
def prune_branches():
    db.connection.close()
    pruned = []
    for branch in Branch.objects.all():
        if not branch.get_github_api():
            branch.delete()
            pruned.append(str(branch))
    if pruned:
        msg = "Pruned branches:\n"
        msg += "\n".join(pruned)
        return msg
    else:
        return "No branches pruned"
