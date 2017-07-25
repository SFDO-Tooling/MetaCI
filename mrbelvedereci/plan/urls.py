from django.conf.urls import url

from mrbelvedereci.plan import views


urlpatterns = [
    url(
        r'^$',
        views.plan_list,
        name='plan_list',
    ),
    url(
        r'^/(?P<plan_id>\w+)/run$',
        views.plan_run,
        name='plan_run',
    ),
    url(
        r'^/(?P<plan_id>\w+)$',
        views.plan_detail,
        name='plan_detail',
    ),
]
