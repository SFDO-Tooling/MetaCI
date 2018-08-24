from django.contrib import admin
from metaci.testresults.models import TestResult
from metaci.testresults.models import TestMethod
from metaci.testresults.models import TestResultAsset

class TestResultAdmin(admin.ModelAdmin):
    list_display = ('build_flow', 'method', 'duration', 'outcome')
    list_filter = ('build_flow__build__repo', 'method', 'method__testclass')
admin.site.register(TestResult, TestResultAdmin)

class TestResultAssetAdmin(admin.ModelAdmin):
    list_display = ('result', 'asset')
    list_filter = ('result__build_flow__build__repo', 'result__method', 'result__method__testclass')
    raw_id_fields = ('result',)
admin.site.register(TestResultAsset, TestResultAssetAdmin)

class TestMethodAdmin(admin.ModelAdmin):
    list_display = ('name', 'testclass')
    list_filter = ('testclass__repo', 'testclass')
admin.site.register(TestMethod, TestMethodAdmin)
