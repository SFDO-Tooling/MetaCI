from django.contrib import admin
from mrbelvedereci.plan.models import Plan
from mrbelvedereci.plan.models import PlanSchedule

class PlanAdmin(admin.ModelAdmin):
    list_display = ('name', 'repo', 'type', 'flows', 'org', 'regex', 'active', 'public')
    list_filter = ('active', 'public', 'type', 'org', 'repo')
admin.site.register(Plan, PlanAdmin)

class PlanScheduleAdmin(admin.ModelAdmin):
    list_display = ('plan', 'branch', 'schedule')
    list_filter = ('plan__repo','schedule')
admin.site.register(PlanSchedule, PlanScheduleAdmin)
