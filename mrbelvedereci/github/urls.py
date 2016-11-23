from django.conf.urls import url

from mrbelvedereci.github import views as github_views

urlpatterns = [
    url(r'^webhook/github/push$', github_views.github_push_webhook),
    url(r'^webhook/github/pull_request$', github_views.github_pull_request_webhook),
]
