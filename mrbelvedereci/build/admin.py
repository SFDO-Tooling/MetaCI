from django.contrib import admin
from mrbelvedereci.build.models import Build
from mrbelvedereci.build.models import BuildFlow

class BuildAdmin(admin.ModelAdmin):
    list_display = ('repo', 'plan', 'branch', 'commit', 'status', 'time_queue', 'time_start', 'time_end')
    list_filter = ('repo', 'plan', 'branch')
admin.site.register(Build, BuildAdmin)

class BuildFlowAdmin(admin.ModelAdmin):
    list_display = ('build', 'status', 'time_queue', 'time_start', 'time_end')
    list_filter = ('build__repo', 'build')
admin.site.register(BuildFlow, BuildFlowAdmin)
