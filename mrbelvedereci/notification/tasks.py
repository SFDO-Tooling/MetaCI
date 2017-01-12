import django_rq
import time
from django.conf import settings
from django.core.cache import cache
from django.core.mail import send_mail
from django.template.loader import get_template
from django.template import Context
from mrbelvedereci.users.models import User
from mrbelvedereci.build.models import Build
from mrbelvedereci.notification.models import RepositoryNotification
from mrbelvedereci.notification.models import BranchNotification
from mrbelvedereci.notification.models import PlanNotification

@django_rq.job('short', timeout=60)
def queue_build_notifications(build_id):
    build = Build.objects.get(id=build_id)

    status_query = {}

    if build.status in ['queued', 'in_progress']:
        return 'Skipping, build not done yet'
    
    if build.status == 'success':
        status_query['on_success'] = True
    elif build.status == 'fail':
        status_query['on_fail'] = True
    elif build.status == 'error':
        status_query['on_error'] = True
    
    repo_notifications = RepositoryNotification.objects.filter(repo = build.repo, **status_query).values('user__id').distinct()
    branch_notifications = BranchNotification.objects.filter(branch = build.branch, **status_query).values('user__id').distinct()
    plan_notifications = PlanNotification.objects.filter(plan = build.plan, **status_query).values('user__id').distinct()

    users_repo = [user['user__id'] for user in repo_notifications]
    users_branch = [user['user__id'] for user in branch_notifications]
    users_plan = [user['user__id'] for user in plan_notifications]

    users = set()
    if users_repo:
        users.update(users_repo)
    if users_branch:
        users.update(users_branch)
    if users_plan:
        users.update(users_plan)

    for user_id in users:
        send_notification_message.delay(build_id, user_id)

    return 'Enqueued send of {} notification messages'.format(len(users))

@django_rq.job('short', timeout=60)
def send_notification_message(build_id, user_id):
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

    subject = '[{}] Build #{} of {} - {}'.format(build.repo.name, build.id, build.branch.name, build.status.upper())
    message = template_txt.render(Context(context))
    html_message_html = template_html.render(Context(context))

    return send_mail(subject, message, settings.FROM_EMAIL, [user.email], html_message=html_message)
