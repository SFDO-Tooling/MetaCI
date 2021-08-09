from django.contrib import admin
from guardian.admin import GuardedModelAdmin

from metaci.plan.models import Plan, PlanRepository, PlanRepositoryTrigger, PlanSchedule


class PlanRepositoryInline(admin.TabularInline):
    model = PlanRepository
    extra = 1


@admin.register(Plan)
class PlanAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "trigger",
        "role",
        "flows",
        "org",
        "regex",
        "commit_status_regex",
        "active",
    )
    list_filter = ("active", "trigger", "role", "org", "repos")
    inlines = [PlanRepositoryInline]


@admin.register(PlanRepository)
class PlanRepositoryAdmin(GuardedModelAdmin):
    list_display = ("repo", "plan", "active")
    list_filter = ("repo", "plan", "active")


@admin.register(PlanRepositoryTrigger)
class PlanRepositoryTriggerAdmin(GuardedModelAdmin):
    list_display = ("target_plan_repo", "source_plan_repo")
    list_filter = ("target_plan_repo", "source_plan_repo")


@admin.register(PlanSchedule)
class PlanScheduleAdmin(GuardedModelAdmin):
    list_display = ("plan", "branch", "schedule")
    list_filter = ("plan", "branch", "schedule")
