from django.conf.urls import re_path

from metaci.repository import views as repository_views

urlpatterns = [
    re_path(
        r"(?P<owner>[-\w]+)/(?P<name>[^/].*)/branch/(?P<branch>.*)$",
        repository_views.branch_detail,
        name="branch_detail",
    ),
    re_path(
        r"(?P<owner>[-\w]+)/(?P<name>[^/].*)/commit/(?P<sha>\w+)$",
        repository_views.commit_detail,
        name="commit_detail",
    ),
    re_path(
        r"(?P<owner>[-\w]+)/(?P<name>[^/].*)/branches",
        repository_views.repo_branches,
        name="repo_branches",
    ),
    re_path(
        r"(?P<owner>[-\w]+)/(?P<name>[^/].*)/plans",
        repository_views.repo_plans,
        name="repo_plans",
    ),
    re_path(
        r"(?P<owner>[-\w]+)/(?P<name>[^/].*)/orgs",
        repository_views.repo_orgs,
        name="repo_orgs",
    ),
    re_path(
        r"(?P<owner>[-\w]+)/(?P<name>[^/].*)/results",
        repository_views.repo_results,
        name="repo_results",
        kwargs={"tab": "results"},
    ),
    re_path(
        r"(?P<owner>[-\w]+)/(?P<name>[^/].*)/*$",
        repository_views.repo_detail,
        name="repo_detail",
    ),
    re_path(
        r"webhook/github/push$",
        repository_views.github_webhook,
        name="github_webhook",
    ),
    re_path(r"$", repository_views.repo_list, name="repo_list"),
]
