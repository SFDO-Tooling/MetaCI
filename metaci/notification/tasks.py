import django_rq
import time
from django import db
from django.conf import settings
from django.core.cache import cache
from django.core.mail import send_mail
from django.template.loader import get_template
from django.template import Context
from metaci.users.models import User
from metaci.build.models import Build
from metaci.notification.models import RepositoryNotification
from metaci.notification.models import BranchNotification
from metaci.notification.models import PlanNotification
from metaci.notification.models import PlanRepositoryNotification
from metaci.plan.models import PlanRepository


def reset_database_connection():
    db.connection.close()

@django_rq.job('short', timeout=60)
def queue_build_notifications(build_id):
    reset_database_connection()

    build = Build.objects.get(id=build_id)

    status_query = {}

    if build.get_status() in ['queued', 'waiting', 'in_progress']:
        return 'Skipping, build not done yet'
    
    if build.get_status() == 'success':
        status_query['on_success'] = True
    elif build.get_status() == 'fail':
        status_query['on_fail'] = True
    elif build.get_status() == 'error':
        status_query['on_error'] = True
    
    repo_notifications = RepositoryNotification.objects.filter(repo = build.repo, **status_query).values('user__id').distinct()
    branch_notifications = BranchNotification.objects.filter(branch = build.branch, **status_query).values('user__id').distinct()
    plan_notifications = PlanNotification.objects.filter(plan = build.plan, **status_query).values('user__id').distinct()
    planrepository = PlanRepository.objects.filter(plan=build.plan, repo=build.repo)[0]
    planrepository_notifications = PlanRepositoryNotification.objects.filter(planrepository=planrepository, **status_query).values('user__id').distinct()

    users_repo = [user['user__id'] for user in repo_notifications]
    users_branch = [user['user__id'] for user in branch_notifications]
    users_plan = [user['user__id'] for user in plan_notifications]
    users_planrepository = [user['user__id'] for user in planrepository_notifications]

    users = set()
    if users_repo:
        users.update(users_repo)
    if users_branch:
        users.update(users_branch)
    if users_plan:
        users.update(users_plan)
    if users_planrepository:
        users.update(users_planrepository)

    for user_id in users:
        send_notification_message.delay(build_id, user_id)

    return 'Enqueued send of {} notification messages'.format(len(users))

@django_rq.job('short', timeout=60)
def send_notification_message(build_id, user_id):
    reset_database_connection()

    build = Build.objects.get(id=build_id)
    user = User.objects.get(id=user_id)

    try:
        log_lines = build.flows.order_by('-date_end')[0].log.split('\n')
    except:
        log_lines = build.log.split('\n')
    log_lines = '\n'.join(log_lines[-25:])

    template_txt = get_template('build/email.txt')
    template_html = get_template('build/email.html')

    context = {
        'build': build,
        'log_lines': log_lines,
    }

    subject = '[{}] Build #{} of {} {} - {}'.format(build.repo.name, build.id, build.branch.name, build.plan.name, build.get_status().upper())
    message = template_txt.render(context)
    html_message = template_html.render(context)

    return send_mail(subject, message, settings.FROM_EMAIL, [user.email], html_message=html_message)
