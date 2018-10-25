from django.conf.urls import url

from metaci.repository import views as repository_views


urlpatterns = [
    url(
        r'(?P<owner>[-\w]+)/(?P<name>[^/].*)/branch/(?P<branch>.*)$',
        repository_views.branch_detail,
        name='branch_detail',
    ),
    url(
        r'(?P<owner>[-\w]+)/(?P<name>[^/].*)/commit/(?P<sha>\w+)$',
        repository_views.commit_detail,
        name='commit_detail',
    ),
    url(
        r'(?P<owner>[-\w]+)/(?P<name>[^/].*)/branches',
        repository_views.repo_branches,
        name='repo_branches',
    ),
    url(
        r'(?P<owner>[-\w]+)/(?P<name>[^/].*)/plans',
        repository_views.repo_plans,
        name='repo_plans',
    ),
    url(
        r'(?P<owner>[-\w]+)/(?P<name>[^/].*)/orgs',
        repository_views.repo_orgs,
        name='repo_orgs',
    ),
    url(
        r'(?P<owner>[-\w]+)/(?P<name>[^/].*)/*$',
        repository_views.repo_detail,
        name='repo_detail',
    ),
    url(
        r'webhook/github/push$',
        repository_views.github_push_webhook,
        name='github_push_webhook',
    ),
    url(
        r'$', repository_views.repo_list,
        name='repo_list',
    ),
]
