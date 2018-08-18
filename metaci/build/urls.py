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
        r'^(?P<build_id>\w+)/rebuilds/(?P<rebuild_id>\w+)/flow_log$',
        views.flow_log_ajax,
        name='flow_log_rebuild_ajax',
    ),
    url(
        r'^(?P<build_id>\w+)/flow_log$',
        views.flow_log_ajax,
        name='flow_log_ajax'
    ),
    url(
        r'^(?P<build_id>\w+)/rebuilds/(?P<rebuild_id>\w+)/(?P<tab>\w+)$',
        views.build_detail,
        name='build_rebuild_detail_tab',
    ),
    url(
        r'^(?P<build_id>\w+)/rebuilds/(?P<rebuild_id>\w+)$',
        views.build_detail,
        name='build_rebuild_detail',
    ),
    url(
        r'^(?P<build_id>\w+)/(?P<tab>\w+)$',
        views.build_detail,
        name='build_detail_tab',
    ),
    url(
        r'^(?P<build_id>\w+)$',
        views.build_detail,
        name='build_detail',
    ),

]
