import hmac
import json
import re

from hashlib import sha1

from django.core.exceptions import PermissionDenied
from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import render
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from metaci.repository.models import Branch
from metaci.repository.models import Repository
from metaci.release.models import Release
from metaci.plan.models import Plan, PlanRepository
from metaci.build.models import Build
from metaci.build.utils import view_queryset


def repo_list(request, owner=None):
    repos = Repository.objects.for_user(request.user)

    if owner:
        repos = repos.filter(owner=owner)

    repo_list = []
    columns = []

    for repo in repos:
        repo_info = {}
        repo_info["name"] = repo.name
        repo_info["owner"] = repo.owner
        repo_info["title"] = str(repo)
        repo_info["build_count"] = repo.builds.for_user(request.user).count()
        repo_info["columns"] = {}
        for plan in repo.plans.for_user(request.user).filter(dashboard__isnull=False):
            if plan.name not in columns:
                columns.append(plan.name)
            builds = []
            latest_builds = plan.builds.filter(repo=repo).order_by("-time_queue")
            if plan.dashboard == "last":
                builds.extend(latest_builds[:1])
            elif plan.dashboard == "recent":
                builds.extend(latest_builds[:5])
            if builds:
                repo_info["columns"][plan.name] = builds
        repo_list.append(repo_info)

    columns.sort()

    for repo in repo_list:
        repo_columns = []
        for column in columns:
            repo_columns.append(repo["columns"].get(column))
        repo["columns"] = repo_columns

    context = {"repos": repo_list, "columns": columns}
    print(context)
    return render(request, "repository/repo_list.html", context=context)


def repo_detail(request, owner, name):
    repo = Repository.objects.get_for_user_or_404(
        request.user, {"owner": owner, "name": name}
    )

    query = {"repo": repo}
    builds = view_queryset(request, query)
    context = {"repo": repo, "builds": builds}
    return render(request, "repository/repo_detail.html", context=context)


def repo_branches(request, owner, name):
    repo = Repository.objects.get_for_user_or_404(
        request.user, {"owner": owner, "name": name}
    )

    context = {"repo": repo}
    return render(request, "repository/repo_branches.html", context=context)


def repo_plans(request, owner, name):
    repo = Repository.objects.get_for_user_or_404(
        request.user, {"owner": owner, "name": name}
    )

    context = {"repo": repo}
    return render(request, "repository/repo_plans.html", context=context)


def repo_orgs(request, owner, name):
    repo = Repository.objects.get_for_user_or_404(
        request.user, {"owner": owner, "name": name}, perms="plan.org_login"
    )

    orgs = repo.orgs.for_user(request.user)

    context = {"orgs": orgs, "repo": repo}
    return render(request, "repository/repo_orgs.html", context=context)


def repo_perf(request, owner, name):
    repo = Repository.objects.get_for_user_or_404(
        request.user, {"owner": owner, "name": name}
    )

    context = {"repo": repo}
    return render(request, "repository/repo_perf.html", context=context)


def branch_detail(request, owner, name, branch):
    repo = Repository.objects.get_for_user_or_404(
        request.user, {"owner": owner, "name": name}
    )

    branch = get_object_or_404(Branch, repo=repo, name=branch)
    query = {"branch": branch}
    builds = view_queryset(request, query)
    context = {"branch": branch, "builds": builds}
    return render(request, "repository/branch_detail.html", context=context)


def commit_detail(request, owner, name, sha):
    repo = Repository.objects.get_for_user_or_404(
        request.user, {"owner": owner, "name": name}
    )

    query = {"commit": sha, "repo": repo}
    builds = view_queryset(request, query)

    context = {"repo": repo, "builds": builds, "commit": sha}
    return render(request, "repository/commit_detail.html", context=context)


def validate_github_webhook(request):
    key = settings.GITHUB_WEBHOOK_SECRET
    signature = request.META.get("HTTP_X_HUB_SIGNATURE").split("=")[1]
    if isinstance(key, str):
        key = key.encode()
    mac = hmac.new(key, msg=request.body, digestmod=sha1)
    if not hmac.compare_digest(mac.hexdigest(), signature):
        raise PermissionDenied()


@csrf_exempt
@require_POST
def github_push_webhook(request):
    validate_github_webhook(request)

    push = json.loads(request.body)
    repo_id = push["repository"]["id"]
    try:
        repo = Repository.objects.get(github_id=repo_id)
    except Repository.DoesNotExist:
        return HttpResponse("Not listening for this repository")

    branch_ref = push.get("ref")
    if not branch_ref:
        return HttpResponse("No branch found")

    branch_name = None
    if branch_ref.startswith("refs/heads/"):
        branch_name = branch_ref.replace("refs/heads/", "")
    elif branch_ref.startswith("refs/tags/"):
        branch_name = branch_ref.replace("refs/tags/", "tag: ")

    if branch_name:
        branch, created = Branch.objects.get_or_create(repo=repo, name=branch_name)
        if branch.is_removed:
            # resurrect the soft deleted branch
            branch.is_removed = False
            branch.save()

    release = None
    # Check if the event was triggered by a tag
    if push["ref"].startswith("refs/tags/") and repo.release_tag_regex:
        tag = push["ref"][len("refs/tags/") :]
        # Check the tag against regex
        if re.match(repo.release_tag_regex, tag) and push["head_commit"]:
            release, _ = Release.objects.get_or_create(
                repo=repo,
                git_tag=tag,
                defaults={
                    "created_from_commit": push["head_commit"]["id"],
                    "status": "draft",
                },
            )

    for pr in repo.planrepository_set.should_run().filter(
        plan__trigger__in=["commit", "tag"]
    ):
        plan = pr.plan
        run_build, commit, commit_message = plan.check_push(push)
        if run_build:
            build = Build(
                repo=repo,
                plan=plan,
                planrepo=pr,
                commit=commit,
                commit_message=commit_message,
                branch=branch,
                build_type="auto",
            )
            if release:
                build.release = release
                build.release_relationship_type = "test"
            build.save()

    return HttpResponse("OK")
