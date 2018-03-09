from django.conf.urls import url

from metaci.notification import views


urlpatterns = [
    url(
        r'^$',
        views.my_notifications,
        name='my_notifications',
    ),
    url(
        r'^add/repository',
        views.add_repository_notification,
        name='add_repository_notification',
    ),
    url(
        r'^add/branch',
        views.add_branch_notification,
        name='add_branch_notification',
    ),
    url(
        r'^add/planrepository',
        views.add_planrepository_notification,
        name='add_planrepository_notification',
    ),
    url(
        r'^add/plan',
        views.add_plan_notification,
        name='add_plan_notification',
    ),
    url(
        r'^delete/branch/(?P<pk>\d+)$',
        views.delete_branch_notification,
        name='delete_branch_notification',
    ),
    url(
        r'^delete/plan/(?P<pk>\d+)$',
        views.delete_plan_notification,
        name='delete_plan_notification',
    ),
    url(
        r'^delete/planrepository/(?P<pk>\d+)$',
        views.delete_planrepository_notification,
        name='delete_planrepository_notification',
    ),
    url(
        r'^delete/repository/(?P<pk>\d+)$',
        views.delete_repository_notification,
        name='delete_repository_notification',
    ),
]
