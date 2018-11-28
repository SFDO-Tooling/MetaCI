from django.contrib import admin
from metaci.repository.models import Branch
from metaci.repository.models import Repository
from metaci.plan.models import PlanRepository


class BranchAdmin(admin.ModelAdmin):
    list_display = ("repo", "name")


admin.site.register(Branch, BranchAdmin)


class PlanRepositoryInline(admin.TabularInline):
    model = PlanRepository


class RepositoryAdmin(admin.ModelAdmin):
    list_display = ("name", "owner")
    inlines = [PlanRepositoryInline]


admin.site.register(Repository, RepositoryAdmin)
