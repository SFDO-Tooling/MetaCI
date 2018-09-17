from django.contrib import admin
from metaci.plan.models import Plan, PlanRepository


class PlanRepositoryInline(admin.TabularInline):
    model = PlanRepository
    extra = 1

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
    inlines = [
        PlanRepositoryInline
    ]
admin.site.register(Plan, PlanAdmin)

class PlanRepositoryAdmin(admin.ModelAdmin):
    list_display = ('repo', 'plan', 'active')
    list_filter = ('repo', 'plan', 'active')
admin.site.register(PlanRepository, PlanRepositoryAdmin)
