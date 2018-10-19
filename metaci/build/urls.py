from django.conf.urls import url

from metaci.build import views


urlpatterns = [
    url(
        r'^$',
        views.build_list,
        name='home',
    ),
    url(
        r'^search$',
        views.build_search,
        name='build_search',
    ),
    url(
        r'^(?P<build_id>\w+)/rebuild$',
        views.build_rebuild,
        name='build_rebuild',
    ),
    url(
        r'^(?P<build_id>\d+)(?:/rebuilds/(?P<rebuild_id>[\d]+|original))?/flows$',
        views.build_detail_flows,
        name='build_detail_flows',
    ),
    url(
        r'^(?P<build_id>\d+)(?:/rebuilds/(?P<rebuild_id>[\d]+|original))?/org$',
        views.build_detail_org,
        name='build_detail_org',
    ),
    url(
        r'^(?P<build_id>\d+)(?:/rebuilds/(?P<rebuild_id>[\d]+|original))?/qa$',
        views.build_detail_qa,
        name='build_detail_qa',
    ),
    url(
        r'^(?P<build_id>\d+)(?:/rebuilds/(?P<rebuild_id>[\d]+|original))?/rebuilds$',
        views.build_detail_rebuilds,
        name='build_detail_rebuilds',
    ),
    url(
        r'^(?P<build_id>\d+)(?:/rebuilds/(?P<rebuild_id>[\d]+|original))?/tests$',
        views.build_detail_tests,
        name='build_detail_tests',
    ),
    url(
        r'^(?P<build_id>\d+)(?:/rebuilds/(?P<rebuild_id>[\d]+|original))?$',
        views.build_detail,
        name='build_detail',
    ),
]
