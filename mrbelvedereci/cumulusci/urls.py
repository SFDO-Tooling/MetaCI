from django.conf.urls import url
from mrbelvedereci.cumulusci import views

urlpatterns = [
    url(r'^/(?P<org_id>\d+)$', views.org_detail, name="org_detail"),
    url(r'^/(?P<org_id>\d+)/login$', views.org_login, name="org_login"),
    url(r'^/(?P<org_id>\d+)/(?P<instance_id>\d+)/login$', views.org_login, name="org_instance_login"),
    url(r'^/(?P<org_id>\d+)/(?P<instance_id>\d+)/delete$', views.org_instance_delete, name="org_instance_delete"),
    url(r'^/(?P<org_id>\d+)/(?P<instance_id>\d+)$', views.org_instance_detail, name="org_instance_detail"),
]
