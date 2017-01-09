from django.conf.urls import url
from mrbelvedereci.trigger import views

urlpatterns = [
    url(r'^$', views.trigger_list, name="trigger_list"),
    url(r'^/(?P<trigger_id>\w+)/run$', views.trigger_run, name="trigger_run"),
    url(r'^/(?P<trigger_id>\w+)$', views.trigger_detail, name="trigger_detail"),
]
