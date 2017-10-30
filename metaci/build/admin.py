from django.contrib import admin
from metaci.build.models import Build
from metaci.build.models import BuildFlow
from metaci.build.models import Rebuild


class BuildAdmin(admin.ModelAdmin):
    list_display = (
        'repo',
        'plan',
        'branch',
        'commit',
        'status',
        'time_queue',
        'time_start',
        'time_end',
    )
    list_filter = ('repo', 'plan', 'branch')
admin.site.register(Build, BuildAdmin)


class BuildFlowAdmin(admin.ModelAdmin):
    list_display = (
        'build',
        'status',
        'time_queue',
        'time_start',
        'time_end',
    )
    list_filter = ('build__repo', 'build')
admin.site.register(BuildFlow, BuildFlowAdmin)


class RebuildAdmin(admin.ModelAdmin):
    list_display = (
        'build',
        'user',
        'status',
        'time_queue',
        'time_start',
        'time_end',
    )
    list_filter = ('build__repo', 'build')
admin.site.register(Rebuild, RebuildAdmin)
