import json
import logging
from collections import defaultdict
from datetime import datetime, timezone
from typing import DefaultDict, List, Optional

from cumulusci.core.dependencies.dependencies import GitHubDynamicDependency
from cumulusci.core.dependencies.resolvers import DependencyResolutionStrategy
from cumulusci.core.github import get_github_api_for_repo
from cumulusci.utils.git import split_repo_url
from django.conf import settings
from django.db.models.query import QuerySet
from django.db.models.signals import post_delete, post_save
from django.dispatch.dispatcher import receiver
from django.urls import reverse
from django.utils.translation import gettext as _
from django_rq import job
from github3.repos.repo import Repository as GitHubRepository
import requests

from metaci.build.models import BUILD_STATUSES, Build
from metaci.cumulusci.keychain import GitHubSettingsKeychain
from metaci.plan.models import PlanRepository
from metaci.release.models import Release, ReleaseCohort
from metaci.repository.models import Repository
from metaci.release.metapush import DependencyGraph, DependencyGraphItem

class DependencyGraphError(Exception):
    pass


def _run_planrepo_for_release(release: Release, planrepo: PlanRepository):
    build = Build(
        repo=release.repo,
        plan=planrepo.plan,
        planrepo=planrepo,
        commit=release.created_from_commit,
        build_type="auto",
        release=release,
        release_relationship_type="automation",
    )
    build.save()
    if release.status != Release.STATUS.inprogress:
        release.status = Release.STATUS.inprogress
        release.save()


def find_active_planrepos_by_role(
    release: Release, role: str
) -> QuerySet[PlanRepository]:
    return release.repo.planrepos.should_run().filter(plan__role=role)


def fail_release_with_message(release: Release, message: str):
    release.error_message = _(message)
    release.status = Release.STATUS.failed
    release.save()

    if release.release_cohort:
        release.release_cohort.error_message = _("One or more releases failed.")
        release.release_cohort.status = Release.STATUS.failed
        release.release_cohort.save()


def _run_release_builds(release: Release):
    """
    Inspect a Release and run the next appropriate Build and maintain Release Status automatically.
    Triggered by a cronjob every minute.
    """

    # NOTE: bug where MetaCI builds can hang in In Progress forever
    # will be painful here.
    def running(builds: List[Build]) -> bool:
        return any(b.status not in Build.COMPLETED_STATUSES for b in builds)

    def last_succeeded(builds: List[Build]) -> bool:
        return (
            bool(builds)
            and not running(builds)
            and builds[-1].status == BUILD_STATUSES.success
        )

    def last_failed(builds: List[Build]) -> bool:
        return (
            bool(builds)
            and not running(builds)
            and builds[-1].status in Build.FAILED_STATUSES
        )

    def any_failed(builds: List[Build]) -> bool:
        return any(b.status in Build.FAILED_STATUSES for b in builds)

    if release.status in [Release.STATUS.failed, Release.STATUS.completed]:
        # Release manager must manually set the status back to In Progress if they're attempting
        # to retry any failed builds.
        return

    # Locate builds associated with this Release.
    # Sort Builds so that we can find the latest of each Role.
    # This supports multi-build retries (rather than rerunning a single Build).
    # Note that our predicates (succeeded() et al.) check for running builds
    # and return False if builds are still running, which is why we can
    # reasonably use `time_end`.

    builds = defaultdict(list)
    for build in release.build_set.filter(
        plan__role__in=["release", "release_deploy", "release_test"]
    ).order_by("time_end"):
        builds[build.plan.role].append(build)

    # Determine what state we are in.

    # Release Test is running or has run.
    if builds["release_test"]:
        if any_failed(builds["release_test"]):
            # Plans may run multiple builds with the role release_test
            # All of them must pass.
            fail_release_with_message(release, "One or more release builds failed.")
        elif last_succeeded(builds["release_test"]):
            release.status = Release.STATUS.completed
            release.save()

        # Either builds are running, or we moved into a completion state.
        # No further action is required.
        return

    # Check our state for the "release" plan
    # Does this repo have an active release_deploy planrepo?
    has_release_deploy = bool(find_active_planrepos_by_role(release, "release_deploy"))

    # We ran, or do not have, release_deploy and need to run "release".
    if not builds["release"] and (not has_release_deploy or builds["release_deploy"]):
        if not has_release_deploy or last_succeeded(builds["release_deploy"]):
            # Locate the "release" plan and planrepo.
            upload_release_planrepos = find_active_planrepos_by_role(release, "release")
            if upload_release_planrepos.count() == 0:
                # This shouldn't happen, but because the user can directly
                # mutate the database, it's possible it's changed since
                # the automated release process started.
                fail_release_with_message(release, "No 'Release' plan is available")
                return

            _run_planrepo_for_release(release, upload_release_planrepos.first())
            return
        elif has_release_deploy and last_failed(builds["release_deploy"]):
            fail_release_with_message(release, "One or more release builds failed.")
            return

    # We have a release_deploy build and it has not yet run.
    if has_release_deploy and not builds["release_deploy"]:
        _run_planrepo_for_release(
            release, find_active_planrepos_by_role(release, "release_deploy").first()
        )

    # The release is running - no new builds required.


# Construct an object we can use as a ProjectConfig equivalent
# for the `flatten()` method. All it needs is the .logger property
# and the method `get_repo_from_url()`.
# This is a bit fragile. TODO: refactor flatten() et al to
# accept an explicitly limited context object.
class NonProjectConfig:
    def get_repo_from_url(self, url: str) -> Optional[GitHubRepository]:
        owner, name = split_repo_url(url)

        return get_github_api_for_repo(
            GitHubSettingsKeychain(), owner, name
        ).repository(owner, name)

    @property
    def logger(self):
        return logging.getLogger(__name__)


def get_dependency_graph(
    releases: List[Release],
) -> DefaultDict[str, List[str]]:
    """Turn a list of Releases into a dependency graph, mapping GitHub repo URLs
    to other GitHub repo URLs on which they depend. Note that the return value
    may include repo URLs that are not part of this Release Cohort or list of
    Releases."""

    # Ensure we have no more than one Release on the same Repo
    urls = [r.repo.url for r in releases]
    if len(urls) != len(set(urls)):
        raise DependencyGraphError(
            "More than one Release on the same Repository is present in the Release Cohort."
        )

    deps = defaultdict(list)
    to_process = [(r.repo.url, r.created_from_commit) for r in releases]
    context = NonProjectConfig()

    while True:
        try:
            (this_dep_url, this_dep_commit) = to_process.pop(0)
        except IndexError:
            break

        # Construct a dependency representing this Release.
        this_dep = GitHubDynamicDependency(github=this_dep_url)
        this_dep.ref = this_dep_commit

        # We're only interested in dependencies on other GitHub repos (== Releases)
        transitive_deps = [
            td
            for td in this_dep.flatten(context)
            if isinstance(td, GitHubDynamicDependency)
        ]
        for transitive_dep in transitive_deps:
            url = str(transitive_dep.github)

            # Add this specific dependency relationship to the graph
            deps[this_dep_url].append(url)

            if url in deps:
                # Already processed, no need to check for deeper transitive deps.
                continue

            if url not in deps and url not in [x[0] for x in to_process]:
                # We need to process this transitive dependency.
                # Find the ref for this dependency
                releases_for_transitive_dep = [r for r in releases if r.repo.url == url]

                # If this is a dependency on a repo that is not in this Cohort,
                # we use None as its ref (resolve to the latest managed release)
                to_process.append(
                    (
                        url,
                        releases_for_transitive_dep[0].created_from_commit
                        if releases_for_transitive_dep
                        else None,
                    )
                )

    return deps


def create_dependency_tree(rc: ReleaseCohort):
    try:
        graph = get_dependency_graph(rc.releases)
    except DependencyGraphError as e:
        rc.status = ReleaseCohort.STATUS.failed
        rc.error_message = str(e)
        rc.save()
        return

    rc.dependency_graph = graph
    rc.save()


def advance_releases(rc: ReleaseCohort):
    dependency_graph = defaultdict(list, rc.dependency_graph or {})
    releases = rc.releases.all()
    for release in releases:
        if release.status not in Release.COMPLETED_STATUSES:
            # Find this Release's dependencies and check if they're satisfied.
            deps = dependency_graph[release.repo.url]
            if release.status == Release.STATUS.inprogress or all_deps_satisfied(
                deps, dependency_graph, releases
            ):
                # This Release is ready to advance.
                _run_release_builds(release)

def is_metapush_enabled():
    return settings.METAPUSH_ENDPOINT_URL and settings.METAPUSH_AUTHENTICATION_TOKEN

def execute_active_release_cohorts():
    # First, identify Release Cohorts that need their dependency trees created.
    for rc in ReleaseCohort.objects.filter(
        status=ReleaseCohort.STATUS.approved, dependency_graph__isnull=True
    ):
        create_dependency_tree(rc)

    # Next, identify in-progress Release Cohorts that have reached a successful conclusion.
    # Release Cohorts whose component Releases fail are updated to a failure state by Release automation.
    for rc in ReleaseCohort.objects.filter(status=ReleaseCohort.STATUS.active).exclude(
        releases__in=Release.objects.exclude(status=Release.STATUS.completed)
    ):
        rc.status = ReleaseCohort.STATUS.completed
        rc.save()

        # Send this Release Cohort to MetaPush for push upgrades, if configured.
        if metapush_enabled() and rc.send_to_metapush:
            send_to_metapush(rc)


    # Next, identify in-progress Release Cohorts that need to be advanced.
    for rc in ReleaseCohort.objects.filter(
        status=ReleaseCohort.STATUS.active
    ).prefetch_related("releases"):
        # This Release Cohort can potentially advance. Grab our dependency graph,
        # then iterate through Releases that are ready to advance and call
        # the function that advances them.
        advance_releases(rc)


execute_active_release_cohorts_job = job(execute_active_release_cohorts)


def all_deps_satisfied(
    deps: List[str], graph: DefaultDict[str, List[str]], releases: List[Release]
) -> bool:
    """Recursively walk the dependency tree to validate that all dependencies are
    either complete or out of scope."""

    releases_dict = {r.repo.url: r for r in releases}

    return all(
        releases_dict[d].status == Release.STATUS.completed
        for d in deps
        if d in releases_dict
    ) and all(
        all_deps_satisfied(graph[d], graph, releases)
        for d in deps
        if d not in releases_dict
    )

PACKAGE_UPLOAD_TASK_PATHS = [
    "cumulusci.tasks.create_package_version.CreatePackageVersion",
    "cumulusci.tasks.salesforce.PackageUpload"
]

def get_package_ids_from_build(build: Build) -> Optional[DependencyGraphItem]:
    """Traverse the Flow Tasks associated with this Build until we locate
    a package upload task. Return a DependencyGraphItem with the package
    details from its output, or None if not found."""
    for build_flow in build.build_flows:
        for flow_task in build_flow.flow_tasks:
            if flow_task.class_path in PACKAGE_UPLOAD_TASK_PATHS:
                # Grab the return values, which will include the 033 and 04t ids
                all_package_id = flow_task.return_values["package_id"]
                # The upload tasks for 1GP and 2GP have different return_values shapes
                all_package_version_id = flow_task.return_values.get("version_id") or flow_task.return_values.get("subscriber_package_version_id")
                if all_package_id and all_package_version_id:
                    return DependencyGraphItem(all_package_id=all_package_id, all_package_version_id=all_package_version_id)


def convert_dependency_graph_to_metapush(rc: ReleaseCohort) -> DependencyGraph:
    """Convert the Release Cohort's dependency graph (expressed in terms of GitHub URLs)
    to a MetaPush-style dependency graph (expressed in terms of 04t and 033 package ids)
    """
    package_versions_to_github_urls = {}
    github_urls_to_package_versions = {}
    dep_graph = DependencyGraph()

    for release in rc.releases:
        if not release.repo.metapush_enabled:
            continue

        github_url = release.repo.url
        # We should have exactly one succeeded Release (Upload Release) build for this Release
        build = release.build_set.filter(plan__role="release", status=BUILD_STATUSES.success).first()
        if not build:
            raise DependencyGraphError("Unable to find Build with role Release on this Release Cohort")

        dep_graph_item = get_package_ids_from_build(build)
        if not dep_graph_item:
            raise DependencyGraphError("Unable to source package details from Build")
        dep_graph.append(dep_graph_item)
        package_versions_to_github_urls[dep_graph_item.all_package_version_id] = github_url
        github_urls_to_package_versions[github_url] = dep_graph_item.all_package_version_id

    # Now, populate the dependencies in the graph.
    for dep_graph_item in dep_graph:
        # Get the GitHub URL for _this_ dependency item
        github_url = package_versions_to_github_urls[dep_graph_item.all_package_version_id]
        # ... get its dependencies from the Release Cohort's graph...
        deps = rc.dependency_graph.get(github_url, [])
        # and convert those GitHub URLs back to created Package Versions
        dep_graph_item.dependencies = []
        for url in deps:
            package_version = github_urls_to_package_versions.get(url)
            if not package_version:
                # This would happen if an intermediate link in the dependency chain
                # is marked metapush_enabled = False
                raise DependencyGraphError("A dependency package version is missing because one or more repositories are not MetaPush-enabled.")
            dep_graph_item.dependencies.append(package_version)

    return dep_graph


@job
def send_to_metapush(rc: ReleaseCohort):
    _send_to_metapush(rc)

def _send_to_metapush(rc: ReleaseCohort):
    token = settings.METAPUSH_AUTHENTICATION_TOKEN
    endpoint = settings.METAPUSH_ENDPOINT_URL

    if endpoint and token:
        # Take our dependency graph (GitHub URL-based) and convert to
        # MetaPush-style 04t/033 id based. MetaPush does not know
        # about repositories - just packages.

        try:
            metapush_graph = convert_dependency_graph_to_metapush(rc)
        except DependencyGraphError as e:
            rc.metapush_error = str(e)
            rc.save()
            return

        # Send the request to MetaPush to create the Push Cohort.
        try:
            requests.post(
                f"{endpoint}/api/pushcohorts/",
                body={
                    "dependency_graph": metapush_graph,
                    "push_schedule": rc.metapush_push_schedule_id
                }
            )
        except Exception as e:
            rc.metapush_error = str(e)
            rc.save()
    else:
        rc.metapush_error = "MetaPush configuration is missing"
        rc.save()
@job
def update_cohort_status() -> str:
    """Run every minute to update Release Cohorts to Active once they pass their start date
    and to Completed once they pass their start date."""

    return _update_release_cohorts()


def _update_release_cohorts() -> str:
    now = datetime.now(tz=timezone.utc)

    # Signals will trigger the updating of merge freezes upon save.
    names_started = []
    for rc in ReleaseCohort.objects.filter(
        status=ReleaseCohort.STATUS.approved,
        merge_freeze_start__lt=now,
        merge_freeze_end__gt=now,
    ).all():
        rc.status = ReleaseCohort.STATUS.active
        rc.save()
        names_started.append(rc.name)

    # Moving into a completed status is handled by release process automation.

    return f"Enabled merge freeze on {', '.join(names_started)}."


def set_merge_freeze_status(repo: Repository, *, freeze: bool):
    # Get all open PRs in this repository
    github_repo = repo.get_github_api()
    for pr in github_repo.pull_requests(state="open", base=github_repo.default_branch):
        # For each PR, get the head commit and apply the freeze status
        set_merge_freeze_status_for_commit(github_repo, pr.head.sha, freeze=freeze)


def set_merge_freeze_status_for_commit(
    repo: GitHubRepository, commit: str, *, freeze: bool
):
    if freeze:
        state = "error"
        description = _("This repository is under merge freeze.")
        target_url = settings.SITE_URL + reverse("cohort_list")
    else:
        state = "success"
        description = ""
        target_url = ""

    repo.create_status(
        sha=commit,
        state=state,
        target_url=target_url,
        description=description,
        context=_("Merge Freeze"),
    )


def release_merge_freeze_if_safe(repo: Repository):
    if not Release.objects.filter(
        repo=repo, release_cohort__status=ReleaseCohort.STATUS.active
    ).count():
        set_merge_freeze_status(repo, freeze=False)


@receiver(post_save, sender=ReleaseCohort)
def react_to_release_cohort_change(instance: ReleaseCohort, **kwargs):
    # We're interested in Release Cohort deletion and updates to the date-time fields and Status.
    # Cohort Creation alone won't trigger merge freeze (associating a Release to the Cohort will)

    # If the Release Cohort is currently in scope, add merge freeze on all of its repos.
    if instance.status == ReleaseCohort.STATUS.active:
        for release in instance.releases.all():
            set_merge_freeze_status(release.repo, freeze=True)
    else:
        # Otherwise, release any merge freezes that are safe to release.
        for release in instance.releases.all():
            release_merge_freeze_if_safe(release.repo)


@receiver(post_save, sender=Release)
def react_to_release_change(instance: Release, **kwargs):
    # Right now, there's no way to cancel a single Release within a Release Cohort
    # (except for deleting the Release object)
    # We need to know if the relationship to Release Cohort changed.

    if kwargs.get("created", False):
        # There is no case where Release creation would lead to lifting merge freeze.
        if (
            instance.release_cohort
            and instance.release_cohort.status == ReleaseCohort.STATUS.active
        ):
            set_merge_freeze_status(instance.repo, freeze=True)
    else:
        # A Release was updated - if it was added to an in-scope Cohort, set merge freeze.
        if (
            instance.release_cohort
            and instance.release_cohort.status == ReleaseCohort.STATUS.active
        ):
            set_merge_freeze_status(instance.repo, freeze=True)
        else:
            # This Release might have been moved from an in-scope release cohort to an out-of-scope Release Cohort or None
            # We don't know if this repo is also included in a different Release that might be in scope, so we can't
            # safely lift merge freeze until we check.
            release_merge_freeze_if_safe(instance.repo)


@receiver(post_delete, sender=Release)
def react_to_release_deletion(instance: Release, **kwargs):
    # This Release might have been moved from an in-scope release cohort to an out-of-scope Release Cohort or None
    # We don't know if this repo is also included in a different Release that might be in scope, so we can't
    # safely lift merge freeze until we check.

    release_merge_freeze_if_safe(instance.repo)
