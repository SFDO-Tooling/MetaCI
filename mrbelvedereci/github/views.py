import hmac
import json
import re

from hashlib import sha1

from django.shortcuts import render
from django.shortcuts import get_object_or_404
from django.conf import settings
from django.http import HttpResponse
from django.http import HttpResponseForbidden
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from mrbelvedereci.github.models import Branch
from mrbelvedereci.github.models import Repository
from mrbelvedereci.trigger.models import Trigger
from mrbelvedereci.build.models import Build

def repo_list(request, owner=None):
    repos = Repository.objects.all()
    if owner:
        repos = repos.filter(owner = owner)

    context = {
        'repos': repos,
    }
    return render(request, 'github/repo_list.html', context=context)

def repo_detail(request, owner, name):
    repo = get_object_or_404(Repository, owner=owner, name=name)
    context = {
        'repo': repo,
    }
    return render(request, 'github/repo_detail.html', context=context)

def branch_detail(request, owner, name, branch):
    repo = get_object_or_404(Repository, owner=owner, name=name)
    branch = get_object_or_404(Branch, repo=repo, name=branch)
    context = {
        'branch': branch,
    }
    return render(request, 'github/branch_detail.html', context=context)

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
    branch, created = Branch.objects.get_or_create(repo=repo, name=branch_name)

    for trigger in repo.triggers.filter(type='commit'):
        if trigger.check_push(push):
            build = Build(
                repo = repo,
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
  
    pull_head = pull_request.get('pull_request', {}).get('head', {}) 

    head_branch_name = pull_head.get('ref')
    if not head_branch_name:
        return HttpResponse('No head branch found')

    head_branch, created = Branch.objects.get_or_create(repo=repo, name=head_branch_name)

    for trigger in repo.triggers.filter(type='pr'):
        if trigger.check_pull_request(pull_request):
            build = Build(
                repo = repo,
                trigger = trigger,
                commit = pull_head['sha'],
                branch = head_branch,
            )
            build.save() 

    return HttpResponse('OK')
