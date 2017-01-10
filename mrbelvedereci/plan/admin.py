from django.contrib import admin
from mrbelvedereci.plan.models import Plan

class PlanAdmin(admin.ModelAdmin):
    list_display = ('name', 'repo', 'type', 'flows', 'org', 'regex', 'active', 'public')
    list_filter = ('active', 'public', 'type', 'org', 'repo')
admin.site.register(Plan, PlanAdmin)
