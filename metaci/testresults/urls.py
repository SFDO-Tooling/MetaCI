from django.conf.urls import url

from metaci.testresults import views


urlpatterns = [
    url(
        r'^(?P<build_id>\d+)/(?P<flow>.*)/compare-to',
        views.build_flow_compare_to,
        name='build_flow_compare_to',
    ),
    url(
        r'^(?P<build_id>\d+)/(?P<flow>.*)$',
        views.build_flow_tests,
        name='build_flow_tests',
    ),
    url(
        r'^trend/method/(?P<method_id>\d+)$',
        views.test_method_trend,
        name='test_method_trend',
    ),
    url(
        r'^method/(?P<method_id>\d+)$',
        views.test_method_peek,
        name='test_method_peek',
    ),
    url(
        r'^result/(?P<result_id>\d+)$',
        views.test_result_detail,
        name='test_result_detail',
    ),
    url(
        r'^result/(?P<result_id>\d+)/robot$',
        views.test_result_robot,
        name='test_result_robot',
    ),
    url(
        r'^compare/$', 
        views.build_flow_compare,
        name='build_flow_compare',
    ),
    url(
        r'dashboard/(?P<repo_owner>[\w-]+)/(?P<repo_name>[\w-]+)/$',
        views.test_dashboard,
        name='test_dashboard'
    ),
    url(
        r'dashboard/(?P<repo_owner>[\w-]+)/(?P<repo_name>[\w-]+)/(?P<test_method_id>\d+)$',
        views.test_dashboard_drill,
        name='test_dashboard'
    )

]
