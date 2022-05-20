from django.urls import re_path

from . import views

app_name = "users"


urlpatterns = [
    re_path(r"^$", views.UserListView.as_view(), name="list"),
    re_path(r"^~redirect/$", views.UserRedirectView.as_view(), name="redirect"),
    re_path(
        r"^(?P<username>[\w.@+-]+)/$",
        views.UserDetailView.as_view(),
        name="detail",
    ),
    re_path(r"^~update/$", views.UserUpdateView.as_view(), name="update"),
]
