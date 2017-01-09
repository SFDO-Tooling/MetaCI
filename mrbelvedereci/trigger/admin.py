from django.contrib import admin
from mrbelvedereci.trigger.models import Trigger

class TriggerAdmin(admin.ModelAdmin):
    list_display = ('name', 'repo', 'type', 'flows', 'org', 'regex', 'active', 'public')
    list_filter = ('active', 'public', 'type', 'org', 'repo')
admin.site.register(Trigger, TriggerAdmin)
