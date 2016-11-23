from django.contrib import admin
from mrbelvedereci.trigger.models import Trigger

class TriggerAdmin(admin.ModelAdmin):
    list_display = ('repo', 'type', 'flows', 'org', 'context')
admin.site.register(Trigger, TriggerAdmin)
