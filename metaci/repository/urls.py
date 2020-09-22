from django.conf.urls import url

from metaci.repository import views as repository_views

urlpatterns = [
    url(
        r"(?P<owner>[-\w]+)/(?P<name>[^/].*)/branch/(?P<branch>.*)$",
        repository_views.branch_detail,
        name="branch_detail",
    ),
    url(
        r"(?P<owner>[-\w]+)/(?P<name>[^/].*)/commit/(?P<sha>\w+)$",
        repository_views.commit_detail,
        name="commit_detail",
    ),
    url(
        r"(?P<owner>[-\w]+)/(?P<name>[^/].*)/branches",
        repository_views.repo_branches,
        name="repo_branches",
    ),
    url(
        r"(?P<owner>[-\w]+)/(?P<name>[^/].*)/plans",
        repository_views.repo_plans,
        name="repo_plans",
    ),
    url(
        r"(?P<owner>[-\w]+)/(?P<name>[^/].*)/orgs",
        repository_views.repo_orgs,
        name="repo_orgs",
    ),
    url(
        r"(?P<owner>[-\w]+)/(?P<name>[^/].*)/perf",
        repository_views.repo_perf,
        name="repo_perf",
        kwargs={"tab": "perf"},
    ),
    url(
        r"(?P<owner>[-\w]+)/(?P<name>[^/].*)/results",
        repository_views.repo_results,
        name="repo_results",
        kwargs={"tab": "results"},
    ),
    url(
        r"(?P<owner>[-\w]+)/(?P<name>[^/].*)/tests",
        repository_views.repo_tests,
        name="repo_tests",
        kwargs={"tab": "tests"},
    ),
    url(
        r"(?P<owner>[-\w]+)/(?P<name>[^/].*)/*$",
        repository_views.repo_detail,
        name="repo_detail",
    ),
    url(
        r"webhook/github/push$",
        repository_views.github_webhook,
        name="github_webhook",
    ),
    url(r"$", repository_views.repo_list, name="repo_list"),
]
