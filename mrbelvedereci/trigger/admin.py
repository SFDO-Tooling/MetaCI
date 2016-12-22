from django.contrib import admin
from mrbelvedereci.trigger.models import Trigger

class TriggerAdmin(admin.ModelAdmin):
    list_display = ('repo', 'type', 'flows', 'org', 'regex', 'active')
admin.site.register(Trigger, TriggerAdmin)
