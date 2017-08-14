from django.contrib import admin
from django.contrib.admin.models import LogEntry, DELETION
from django.utils.html import escape
from django.core.urlresolvers import reverse
from mrbelvedereci.build.models import Build
from mrbelvedereci.build.models import BuildFlow
from mrbelvedereci.build.models import Rebuild


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



class LogEntryAdmin(admin.ModelAdmin):

    date_hierarchy = 'action_time'


    list_filter = [
        'user',
        'content_type',
        'action_flag'
    ]

    search_fields = [
        'object_repr',
        'change_message'
    ]


    list_display = [
        'action_time',
        'user',
        'content_type',
        'object_link',
        'action_flag',
        'change_message',
    ]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser and request.method != 'POST'

    def has_delete_permission(self, request, obj=None):
        return False

    def object_link(self, obj):
        if obj.action_flag == DELETION:
            link = escape(obj.object_repr)
        else:
            ct = obj.content_type
            link = u'<a href="%s">%s</a>' % (
                reverse('admin:%s_%s_change' % (ct.app_label, ct.model), args=[obj.object_id]),
                escape(obj.object_repr),
            )
        return link
    object_link.allow_tags = True
    object_link.admin_order_field = 'object_repr'
    object_link.short_description = u'object'
    
    def queryset(self, request):
        return super(LogEntryAdmin, self).queryset(request) \
            .prefetch_related('content_type')


admin.site.register(LogEntry, LogEntryAdmin)