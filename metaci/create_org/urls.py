from django.conf.urls import re_path

from metaci.create_org import views as create_org_views

urlpatterns = [
    re_path(r"scratch$", create_org_views.scratch_org, name="create_org_scratch"),
    re_path(r"qa$", create_org_views.qa_org, name="create_org_qa"),
    re_path(r"$", create_org_views.create_org, name="create_org"),
]
