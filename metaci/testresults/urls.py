from django.conf.urls import re_path

from metaci.testresults import views

urlpatterns = [
    re_path(
        r"^(?P<build_id>\d+)/(?P<flow>.*)/compare-to",
        views.build_flow_compare_to,
        name="build_flow_compare_to",
    ),
    re_path(
        r"^(?P<build_id>\d+)/(?P<flow>.*)/download-asset/(?P<build_flow_asset_id>.*)$",
        views.build_flow_download_asset,
        name="build_flow_download_asset",
    ),
    re_path(
        r"^(?P<build_id>\d+)/(?P<flow>.*)$",
        views.build_flow_tests,
        name="build_flow_tests",
    ),
    re_path(
        r"^trend/method/(?P<method_id>\d+)$",
        views.test_method_trend,
        name="test_method_trend",
    ),
    re_path(
        r"^method/(?P<method_id>\d+)$", views.test_method_peek, name="test_method_peek"
    ),
    re_path(
        r"^result/(?P<result_id>\d+)$",
        views.test_result_detail,
        name="test_result_detail",
    ),
    re_path(
        r"^result/(?P<result_id>\d+)/robot$",
        views.test_result_robot,
        name="test_result_robot",
    ),
    re_path(
        r"^result/(?P<result_id>\d+)/download-asset/(?P<testresult_asset_id>.*)$",
        views.testresult_download_asset,
        name="testresult_download_asset",
    ),
    re_path(r"^compare/$", views.build_flow_compare, name="build_flow_compare"),
]
