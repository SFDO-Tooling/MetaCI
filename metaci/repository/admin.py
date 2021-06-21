from django.contrib import admin

from metaci.plan.models import PlanRepository
from metaci.repository.models import Branch, Repository


@admin.register(Branch)
class BranchAdmin(admin.ModelAdmin):
    list_display = ("repo", "name")


class PlanRepositoryInline(admin.TabularInline):
    model = PlanRepository


@admin.register(Repository)
class RepositoryAdmin(admin.ModelAdmin):
    list_display = ("name", "owner")
    inlines = [PlanRepositoryInline]
