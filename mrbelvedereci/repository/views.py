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
from mrbelvedereci.repository.models import Branch
from mrbelvedereci.repository.models import Repository
from mrbelvedereci.plan.models import Plan
from mrbelvedereci.build.models import Build
from mrbelvedereci.build.utils import view_queryset

def repo_list(request, owner=None):
    repos = Repository.objects.all()

    if not request.user.is_staff:
        repos = repos.filter(public = True)
    if owner:
        repos = repos.filter(owner = owner)

    context = {
        'repos': repos,
    }
    return render(request, 'repository/repo_list.html', context=context)

def repo_detail(request, owner, name):
    query = {
        'owner': owner,
        'name': name,
    }
    if not request.user.is_staff:
        query['public'] = True
    repo = get_object_or_404(Repository, **query)

    query = {'repo': repo}
    builds = view_queryset(request, query)
    context = {
        'repo': repo,
        'builds': builds,
    }
    return render(request, 'repository/repo_detail.html', context=context)

def repo_branches(request, owner, name):
    query = {
        'owner': owner,
        'name': name,
    }
    if not request.user.is_staff:
        query['public'] = True
    repo = get_object_or_404(Repository, **query)

    context = {
        'repo': repo,
    }
    return render(request, 'repository/repo_branches.html', context=context)

def repo_plans(request, owner, name):
    query = {
        'owner': owner,
        'name': name,
    }
    if not request.user.is_staff:
        query['public'] = True
    repo = get_object_or_404(Repository, **query)

    context = {
        'repo': repo,
    }
    return render(request, 'repository/repo_plans.html', context=context)

def branch_detail(request, owner, name, branch):
    query = {
        'owner': owner,
        'name': name,
    }
    if not request.user.is_staff:
        query['public'] = True
    repo = get_object_or_404(Repository, **query)

    branch = get_object_or_404(Branch, repo=repo, name=branch)
    query = {'branch': branch}
    builds = view_queryset(request, query)
    context = {
        'branch': branch,
        'builds': builds,
    }
    return render(request, 'repository/branch_detail.html', context=context)

def commit_detail(request, owner, name, sha):
    query = {
        'owner': owner,
        'name': name,
    }
    if not request.user.is_staff:
        query['public'] = True
    repo = get_object_or_404(Repository, **query)
    
    query = {'commit': sha, 'repo': repo}
    builds = view_queryset(request, query)

    context = {
        'repo': repo,
        'builds': builds,
        'commit': sha,
    }
    return render(request, 'repository/commit_detail.html', context=context)

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

    branch_name = None
    if branch_ref.startswith('refs/heads/'):
        branch_name = branch_ref.replace('refs/heads/','')
    elif branch_ref.startswith('refs/tags/'):
        branch_name = branch_ref.replace('refs/tags/', 'tag: ')

    if branch_name:
        branch, created = Branch.objects.get_or_create(repo=repo, name=branch_name)

    for plan in repo.plans.filter(type__in=['commit', 'tag'], active=True):
        run_build, commit = plan.check_push(push)
        if run_build:
            build = Build(
                repo = repo,
                plan = plan,
                commit = commit,
                branch = branch,
            )
            build.save() 

    return HttpResponse('OK')
