from django.conf.urls import re_path

from metaci.notification import views

urlpatterns = [
    re_path(r"^$", views.my_notifications, name="my_notifications"),
    re_path(
        r"^add/repository",
        views.AddRepositoryNotification.as_view(),
        name="add_repository_notification",
    ),
    re_path(
        r"^add/branch",
        views.AddBranchNotification.as_view(),
        name="add_branch_notification",
    ),
    re_path(
        r"^add/planrepository",
        views.AddPlanRepositoryNotification.as_view(),
        name="add_planrepository_notification",
    ),
    re_path(
        r"^add/plan", views.AddPlanNotification.as_view(), name="add_plan_notification"
    ),
    re_path(
        r"^delete/branch/(?P<pk>\d+)$",
        views.DeleteBranchNotification.as_view(),
        name="delete_branch_notification",
    ),
    re_path(
        r"^delete/plan/(?P<pk>\d+)$",
        views.DeletePlanNotification.as_view(),
        name="delete_plan_notification",
    ),
    re_path(
        r"^delete/planrepository/(?P<pk>\d+)$",
        views.DeletePlanRepositoryNotification.as_view(),
        name="delete_planrepository_notification",
    ),
    re_path(
        r"^delete/repository/(?P<pk>\d+)$",
        views.DeleteRepositoryNotification.as_view(),
        name="delete_repository_notification",
    ),
]
