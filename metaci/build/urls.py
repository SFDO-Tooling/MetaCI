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
        r'^(?P<build_id>\d+)(?:/rebuilds/(?P<rebuild_id>[\d]+|original))?(?:/(?P<tab>\w+))?$',
        views.build_detail,
        name='build_detail',
    ),
]
