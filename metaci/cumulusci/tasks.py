from django import db
from django.utils import timezone
from django_rq import job

from metaci.cumulusci.models import ScratchOrgInstance


import requests


@job("short")
def prune_orgs():
    """An RQ task to mark expired orgs as deleted.

    We don't need to bother calling delete_org on each expired scratch
    org, we'll trust that the org expires, and just efficiently flip the
    bits in MetaCI so that they don't show up on list views anymore.
    """
    db.connection.close()
    pruneing_qs = ScratchOrgInstance.expired.all()
    count = pruneing_qs.update(
        deleted=True, time_deleted=timezone.now(), delete_error="Org is expired."
    )
    return f"pruned {count} orgs"


def onboard_persistent_org():
    response = requests.get("{}/services/oauth2/authorize")
