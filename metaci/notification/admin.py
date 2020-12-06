from django.contrib import admin

from metaci.notification.models import (
    BranchNotification,
    PlanNotification,
    PlanRepositoryNotification,
    RepositoryNotification,
)


@admin.register(RepositoryNotification)
class RepositoryNotificationAdmin(admin.ModelAdmin):
    list_display = ("target", "user")
    list_filter = ("target", "user")


@admin.register(BranchNotification)
class BranchNotificationAdmin(admin.ModelAdmin):
    list_display = ("target", "user")
    list_filter = ("target__repo", "user")


@admin.register(PlanNotification)
class PlanNotificationAdmin(admin.ModelAdmin):
    list_display = ("target", "user")
    list_filter = ("target__repos", "user")


@admin.register(PlanRepositoryNotification)
class PlanRepositoryNotificationAdmin(admin.ModelAdmin):
    list_display = ("target", "user")
    list_filter = ("target__repo", "user")
