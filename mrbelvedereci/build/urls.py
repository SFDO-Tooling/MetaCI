from django.conf.urls import url
from mrbelvedereci.build import views

urlpatterns = [
    url(r'^$', views.build_list),
    url(r'^/(?P<build_id>\w+)$', views.build_detail),
]
