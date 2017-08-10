from django.conf.urls import url

from mrbelvedereci.testresults import views


urlpatterns = [
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
        r'^compare/$', 
        views.build_flow_compare,
        name='build_flow_compare',
    ),
    url(
        r'^(?P<build_id>\d+)/(?P<flow>.*)/compare_to',
        views.build_flow_compare_to,
        name='build_flow_compare_to',
    )
]
