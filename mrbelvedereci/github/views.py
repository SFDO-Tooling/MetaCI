import hmac
import json
import re

from hashlib import sha1

from django.shortcuts import render
from django.conf import settings
from django.http import HttpResponse
from django.http import HttpResponseForbidden
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from mrbelvedereci.github.models import Branch
from mrbelvedereci.github.models import Repository
from mrbelvedereci.trigger.models import Trigger
from mrbelvedereci.build.models import Build

def validate_github_webhook(request):
    key = settings.GITHUB_WEBHOOK_SECRET
    signature = request.META.get('HTTP_X_HUB_SIGNATURE').split('=')[1]
    if type(key) == unicode:
        key = key.encode()
    mac = hmac.new(key, msg=request.body, digestmod=sha1)
    if not hmac.compare_digest(mac.hexdigest(), signature):
        return False
    return True

@csrf_exempt
@require_POST
def github_push_webhook(request):
    if not validate_github_webhook(request):
        return HttpResponseForbidden

    push = json.loads(request.body)
    repo_id = push['repository']['id']
    try:
        repo = Repository.objects.get(github_id = repo_id)
    except Repository.DoesNotExist:
        return HttpResponse('Not listening for this repository')
   
    branch_ref = push.get('ref')
    if not branch_ref:
        return HttpResponse('No branch found')

    branch_name = branch_ref.replace('refs/heads/','')
    branch = Branch.objects.get_or_create(repo=repo, name=branch_name)

    for trigger in repo.triggers:
        if trigger.check_push(push):
            build = Build(
                trigger = trigger,
                commit = push['after'],
                branch = branch,
            )
            build.save() 

    return HttpResponse('OK')

@csrf_exempt
@require_POST
def github_pull_request_webhook(request):
    if not validate_github_webhook(request):
        return HttpResponseForbidden

    pull_request = json.loads(request.body)
    repo_id = pull_request['repository']['id']
    try:
        repo = Repository.objects.get(github_id = repo_id)
    except Repository.DoesNotExist:
        return HttpResponse('Not listening for this repository')
  
    pull_base = pull_request.get('pull_request', {}).get('base', {}) 
    pull_head = pull_request.get('pull_request', {}).get('head', {}) 

    head_branch_name = pull_base.get('ref')
    if not head_branch_ref:
        return HttpResponse('No head branch found')

    head_branch = Branch.objects.get_or_create(repo=repo, name=head_branch_name)

    for trigger in repo.triggers:
        if trigger.check_pull_request(pull_request):
            build = Build(
                trigger = trigger,
                commit = pull_head['sha'],
                branch = head_branch,
            )
            build.save() 

    return HttpResponse('OK')
