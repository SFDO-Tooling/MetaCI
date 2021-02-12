from django.conf.urls import re_path

from metaci.hirefire import views

urlpatterns = [
    re_path(r"^test$", views.test, name="test"),
    re_path(r"^(?P<token>.*)/info$", views.info, name="info"),
]
