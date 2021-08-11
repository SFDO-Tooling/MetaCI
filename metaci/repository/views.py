import hmac
import json
import logging
import re
from hashlib import sha1

from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from metaci.build.models import Build
from metaci.build.utils import view_queryset
from metaci.release.models import Release
from metaci.repository.models import Branch, Repository

logger = logging.getLogger(__name__)

TAG_BRANCH_PREFIX = "refs/tags/"


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


def repo_perf(request, owner, name, tab):
    repo = Repository.objects.get_for_user_or_404(
        request.user, {"owner": owner, "name": name}
    )

    context = {"repo": repo, "tab": tab}
    return render(request, "repository/repo_perf.html", context=context)


def repo_results(request, owner, name, tab):
    repo = Repository.objects.get_for_user_or_404(
        request.user, {"owner": owner, "name": name}
    )

    context = {"repo": repo, "tab": tab}
    return render(request, "repository/repo_results.html", context=context)


repo_tests = repo_perf


def branch_detail(request, owner, name, branch):
    repo = Repository.objects.get_for_user_or_404(
        request.user, {"owner": owner, "name": name}
    )

    branch = get_object_or_404(Branch, repo=repo, name=branch)
    query = {"branch": branch}
    builds = view_queryset(request, query)
    context = {"branch": branch, "builds": builds, "repo": repo}
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
def github_webhook(request):
    validate_github_webhook(request)
    event = request.META.get("HTTP_X_GITHUB_EVENT")
    payload = json.loads(request.body)

    try:
        repo = get_repository(payload)
    except Repository.DoesNotExist:
        return HttpResponse("Not listening for this repository")

    branch_name = get_branch_name_from_payload(payload)

    if not branch_name:
        return HttpResponse("No branch found")

    branch = get_or_create_branch(branch_name, repo)
    release = get_release_if_applicable(payload, repo)
    create_builds(event, payload, repo, branch, release)

    return HttpResponse("OK")


def get_repository(event):
    repo_id = event["repository"]["id"]
    return Repository.objects.get(github_id=repo_id)


def get_branch_name_from_payload(event):
    branches = event.get("branches")
    if branches:
        branch_name = event["branches"][0]["name"]
        return branch_name

    branch_ref = event.get("ref")
    if not branch_ref:
        return None

    branch_name = None
    if branch_ref.startswith("refs/heads/"):
        branch_name = branch_ref.replace("refs/heads/", "")
    elif branch_ref.startswith(TAG_BRANCH_PREFIX):
        branch_name = branch_ref.replace(TAG_BRANCH_PREFIX, "tag: ")
    return branch_name


def get_or_create_branch(branch_name, repo):
    branch, _ = Branch.objects.get_or_create(repo=repo, name=branch_name)
    if branch.is_removed:
        # resurrect the soft deleted branch
        branch.is_removed = False
        branch.save()

    return branch


def create_builds(event, payload, repo, branch, release):
    for pr in repo.planrepository_set.should_run().filter(
        plan__trigger__in=["commit", "tag", "status"]
    ):
        plan = pr.plan
        run_build, commit, commit_message = plan.check_github_event(event, payload)
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


def is_tag(ref):
    """Returns true if ref corresponds to a tag. False otherwise"""
    return True if ref.startswith(TAG_BRANCH_PREFIX) else False


def get_release_if_applicable(event, repo):
    """Gets the corresponding release if 'ref' references a release tag"""
    if "ref" not in event:
        return

    release = None
    if is_tag(event["ref"]) and repo.release_tag_regex:
        tag = get_tag_name_from_ref(event["ref"])
        if tag_is_release(tag, repo) and event["head_commit"]:
            release = Release.objects.filter(repo=repo, git_tag=tag).first()
    return release


def tag_is_release(tag, repo):
    return re.match(repo.release_tag_regex, tag)


def get_tag_name_from_ref(ref):
    return ref[len(TAG_BRANCH_PREFIX) :]
