import requests
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.admin.models import LogEntry, ADDITION
from django.contrib.contenttypes.models import ContentType
from github3 import login
from mrbelvedereci.plan.models import Plan
from mrbelvedereci.build.models import Build


@receiver(post_save, sender=Build)
def log_manual_build(sender, **kwargs):
    # skip updates
    if not kwargs['created']:
        return

    build = kwargs['instance']

    # Log the new build and who created it.
    LogEntry.objects.log_action(
            user_id = build.user.id,
            content_type_id = ContentType.objects.get_for_model(build).id,
            object_id = build.id,
            object_repr = build.__str__(),
            change_message = 'started a build',
            action_flag = ADDITION,
    )


@receiver(post_save, sender=Plan)
def create_plan_webhooks(sender, **kwargs):
    # Skip updates
    if not kwargs['created']:
        return

    plan = kwargs['instance']

    # Skip manual plans
    if plan.type == 'manual':
        return

    event = 'push'
    if plan.type == 'pr':
        event = 'pull_request'

    callback_url = '{}/{}'.format(settings.GITHUB_WEBHOOK_BASE_URL, event)

    plan = kwargs['instance']
  
    # Initialize repo API 
    github = login(settings.GITHUB_USERNAME, settings.GITHUB_PASSWORD)
    repo = github.repository(plan.repo.owner, plan.repo.name)

    # Check if webhook exists for repo
    existing = False
    for hook in repo.iter_hooks():
        if hook.config.get('url') == callback_url and event in hook.events:
            existing = True

    # If no webhook, create it 
    if not existing:
        repo.create_hook(
            name = 'web',
            events = [event],
            config = {
                'url': callback_url,
                'content_type': 'json',
                'secret': settings.GITHUB_WEBHOOK_SECRET,
            },
        )
