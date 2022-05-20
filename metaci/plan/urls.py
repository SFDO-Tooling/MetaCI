from django.urls import re_path

from metaci.plan import views

urlpatterns = [
    re_path(r"^$", views.plan_list, name="plan_list"),
    re_path(r"^(?P<plan_id>\w+)/run$", views.plan_run, name="plan_run"),
    re_path(
        r"^(?P<plan_id>\w+)/(?P<repo_owner>[\w-]+)/(?P<repo_name>[\w-]+)/run/$",
        views.plan_run_repo,
        name="plan_run_repo",
    ),
    re_path(r"^(?P<plan_id>\w+)$", views.plan_detail, name="plan_detail"),
    re_path(
        r"^(?P<plan_id>\w+)/(?P<repo_owner>[\w-]+)/(?P<repo_name>[\w-]+)$",
        views.plan_detail_repo,
        name="plan_detail_repo",
    ),
]
