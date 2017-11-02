from django.conf.urls import url

from metaci.plan import views


urlpatterns = [
    url(
        r'^$',
        views.plan_list,
        name='plan_list',
    ),
    url(
        r'^(?P<plan_id>\w+)/run$',
        views.plan_run,
        name='plan_run',
    ),
    url(
        r'^(?P<plan_id>\w+)/(?P<repo_owner>[\w-]+)/(?P<repo_name>[\w-]+)/run/$',
        views.plan_run_repo,
        name='plan_run_repo',
    ),
    url(
        r'^(?P<plan_id>\w+)$',
        views.plan_detail,
        name='plan_detail',
    ),
    url(
        r'^(?P<plan_id>\w+)/(?P<repo_owner>[\w-]+)/(?P<repo_name>[\w-]+)/$',
        views.plan_detail_repo,
        name='plan_detail_repo',
    ),
]
