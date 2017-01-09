from django.contrib import admin
from mrbelvedereci.trigger.models import Trigger

class TriggerAdmin(admin.ModelAdmin):
    list_display = ('repo', 'type', 'flows', 'org', 'regex', 'active', 'public')
    list_filter = ('active', 'public', 'repo', 'org', 'type')
admin.site.register(Trigger, TriggerAdmin)
