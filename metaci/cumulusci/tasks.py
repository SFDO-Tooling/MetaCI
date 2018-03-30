from django import db
from django_rq import job

from metaci.cumulusci.models import ScratchOrgInstance


@job('short')
def prune_orgs():
    db.connection.close()
    pruned = []
    for soi in ScratchOrgInstance.expired.all():
        soi.delete()
        pruned.append(str(soi))
    if pruned:
        msg = 'Pruned orgs:\n'
        msg += '\n'.join(pruned)
        return msg
    else:
        return 'No orgs pruned'