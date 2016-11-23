import requests
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver
from github3 import login
from mrbelvedereci.trigger.models import Trigger

@receiver(post_save, sender=Trigger)
def create_trigger_webhooks(sender, **kwargs):
    # Skip updates
    if not kwargs['created']:
        return

    trigger = kwargs['instance']

    # Skip manual triggers
    if trigger.type == 'manual':
        return

    event = 'push'
    if trigger.type == 'pr':
        event = 'pull_request'

    callback_url = '{}/{}'.format(settings.GITHUB_WEBHOOK_BASE_URL, event)

    trigger = kwargs['instance']
  
    # Initialize repo API 
    github = login(settings.GITHUB_USERNAME, settings.GITHUB_PASSWORD)
    repo = github.repository(trigger.repo.owner, trigger.repo.name)

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
