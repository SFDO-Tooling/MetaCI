import requests
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver
from github3 import login

from mrbelvedereci.plan.models import PlanRepository
from mrbelvedereci.plan.tasks import create_github_webhook


@receiver(post_save, sender=PlanRepository)
def handle_planrepository_save(sender, **kwargs):
    plan_repo = kwargs['instance']
    if plan_repo.plan.type != 'manual':
        create_github_webhook.delay(plan_repo.pk)
