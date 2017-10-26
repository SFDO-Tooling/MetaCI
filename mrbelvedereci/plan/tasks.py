import django_rq
from django import db
from django.conf import settings

from mrbelvedereci.plan.models import PlanRepository
from mrbelvedereci.plan.models import PlanSchedule

def reset_database_connection():
    db.connection.close()

def run_scheduled(schedule):
    reset_database_connection()

    schedules = PlanSchedule.objects.filter(schedule=schedule)
   
    log = [] 
    log.append('Found {} {} schedules to run'.format(schedules.count(), schedule))

    for sched in schedules:
        try:
            build = sched.run()
            log.append('Created build #{} from Plan {} on branch {}'.format(build.id, sched.plan, sched.branch))
    
        except Exception as e:
            log.append('Schedule {} failed with error:\n{}'.format(sched, unicode(e)))

    return '\n'.join(log)

@django_rq.job('short')
def run_scheduled_daily():
    return run_scheduled('daily')

@django_rq.job('short')
def run_scheduled_hourly():
    return run_scheduled('hourly')

@django_rq.job('short')
def create_github_webhook(pk):
    """Create a webhook if it doesn't exist yet."""
    plan_repo = PlanRepository.objects.get(pk=pk)
    event = 'pull_request' if plan_repo.plan.type == 'pr' else 'push'
    callback_url = '{}/{}'.format(settings.GITHUB_WEBHOOK_BASE_URL, event)
    exists = False
    gh_repo = plan_repo.repo.github_api
    for hook in gh_repo.iter_hooks():
        if hook.config.get('url') == callback_url and event in hook.events:
            exists = True
            break
    if not exists:
        gh_repo.create_hook(
            name='web',
            events=[event],
            config={
                'url': callback_url,
                'content_type': 'json',
                'secret': settings.GITHUB_WEBHOOK_SECRET,
            },
        )
