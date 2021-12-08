from django.conf.urls import re_path

from metaci.cumulusci import views

urlpatterns = [
    re_path(r"^request_pooled_org$", views.request_pooled_org, name="org_request"),
    re_path(r"^(?P<org_id>\d+)$", views.org_detail, name="org_detail"),
    re_path(r"^(?P<org_id>\d+)/lock$", views.org_lock, name="org_lock"),
    re_path(r"^(?P<org_id>\d+)/unlock$", views.org_unlock, name="org_unlock"),
    re_path(r"^(?P<org_id>\d+)/login$", views.org_login, name="org_login"),
    re_path(
        r"^(?P<org_id>\d+)/(?P<instance_id>\d+)/login$",
        views.org_login,
        name="org_instance_login",
    ),
    re_path(
        r"^(?P<org_id>\d+)/(?P<instance_id>\d+)/delete$",
        views.org_instance_delete,
        name="org_instance_delete",
    ),
    re_path(
        r"^(?P<org_id>\d+)/(?P<instance_id>\d+)$",
        views.org_instance_detail,
        name="org_instance_detail",
    ),
    re_path(r"^$", views.org_list, name="org_list"),
]
