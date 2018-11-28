from django.conf.urls import url

from metaci.create_org import views as create_org_views


urlpatterns = [
    url(r"scratch$", create_org_views.scratch_org, name="create_org_scratch"),
    url(r"qa$", create_org_views.qa_org, name="create_org_qa"),
    url(r"$", create_org_views.create_org, name="create_org"),
]
