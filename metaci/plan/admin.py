from django.contrib import admin
from metaci.plan.models import Plan
from metaci.plan.models import PlanRepository
from metaci.plan.models import PlanSchedule

class PlanAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'type',
        'flows',
        'org',
        'regex',
        'active',
        'public',
    )
    list_filter = (
        'active',
        'public',
        'type',
        'org',
        'repos',
    )
admin.site.register(Plan, PlanAdmin)

class PlanRepositoryAdmin(admin.ModelAdmin):
    list_display = ('repo', 'plan')
    list_filter = ('repo', 'plan')
admin.site.register(PlanRepository, PlanRepositoryAdmin)

class PlanScheduleAdmin(admin.ModelAdmin):
    list_display = ('plan', 'branch', 'schedule')
    list_filter = ('plan__repos', 'schedule')
admin.site.register(PlanSchedule, PlanScheduleAdmin)
