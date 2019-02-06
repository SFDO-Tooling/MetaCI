from django.contrib import admin
from metaci.plan.models import Plan, PlanRepository, PlanRepositoryTrigger
from guardian.admin import GuardedModelAdmin


class PlanRepositoryInline(admin.TabularInline):
    model = PlanRepository
    extra = 1


class PlanAdmin(admin.ModelAdmin):
    list_display = ("name", "trigger", "role", "flows", "org", "regex", "active")
    list_filter = ("active", "trigger", "role", "org", "repos")
    inlines = [PlanRepositoryInline]


admin.site.register(Plan, PlanAdmin)


class PlanRepositoryAdmin(GuardedModelAdmin):
    list_display = ("repo", "plan", "active")
    list_filter = ("repo", "plan", "active")


admin.site.register(PlanRepository, PlanRepositoryAdmin)


class PlanRepositoryTriggerAdmin(GuardedModelAdmin):
    list_display = ("repo", "plan_repo", "active")
    list_filter = ("repo", "plan_repo", "active")


admin.site.register(PlanRepositoryTrigger, PlanRepositoryTriggerAdmin)
