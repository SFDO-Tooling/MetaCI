from django.conf.urls import url
from mrbelvedereci.notification import views

urlpatterns = [
    url(r'^$', views.my_notifications, name="my_notifications"),
    url(r'^/add/repository', views.add_repository_notification, name="add_repository_notification"),
    url(r'^/add/branch', views.add_branch_notification, name="add_branch_notification"),
    url(r'^/add/plan', views.add_plan_notification, name="add_plan_notification"),
]
