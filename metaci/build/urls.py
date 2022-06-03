from django.urls import re_path

from metaci.build import views

urlpatterns = [
    re_path(
        r"^$",
        views.build_list,
        name="home",
    ),
    re_path(
        r"^search$",
        views.build_search,
        name="build_search",
    ),
    re_path(
        r"^(?P<build_id>\w+)/rebuild$",
        views.build_rebuild,
        name="build_rebuild",
    ),
    re_path(
        r"^(?P<build_id>\d+)(?:/rebuilds/(?P<rebuild_id>[\d]+|original))?/flows$",
        views.build_detail_flows,
        name="build_detail_flows",
    ),
    re_path(
        r"^(?P<build_id>\d+)(?:/rebuilds/(?P<rebuild_id>[\d]+|original))?/org$",
        views.build_detail_org,
        name="build_detail_org",
    ),
    re_path(
        r"^(?P<build_id>\d+)(?:/rebuilds/(?P<rebuild_id>[\d]+|original))?/qa$",
        views.build_detail_qa,
        name="build_detail_qa",
    ),
    re_path(
        r"^(?P<build_id>\d+)(?:/rebuilds/(?P<rebuild_id>[\d]+|original))?/rebuilds$",
        views.build_detail_rebuilds,
        name="build_detail_rebuilds",
    ),
    re_path(
        r"^(?P<build_id>\d+)(?:/rebuilds/(?P<rebuild_id>[\d]+|original))?/tests$",
        views.build_detail_tests,
        name="build_detail_tests",
    ),
    re_path(
        r"^(?P<build_id>\d+)(?:/rebuilds/(?P<rebuild_id>[\d]+|original))?$",
        views.build_detail,
        name="build_detail",
    ),
]
