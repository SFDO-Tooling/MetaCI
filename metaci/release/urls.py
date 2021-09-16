from django.conf.urls import re_path

from metaci.release import views

urlpatterns = [
    re_path(
        r"^$",
        views.cohort_list,
        name="home"
    ),
    re_path(
        r"^(?P<cohort_id>\w+)$",
        views.cohort_detail,
        name="home"
    ),
]