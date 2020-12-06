from django.contrib import admin

from metaci.build.models import Build, BuildFlow, FlowTask, Rebuild


@admin.register(Build)
class BuildAdmin(admin.ModelAdmin):
    list_display = (
        "repo",
        "plan",
        "branch",
        "commit",
        "status",
        "time_queue",
        "time_start",
        "time_end",
    )
    list_filter = ("repo", "plan")
    list_select_related = ("branch", "repo", "plan")

    raw_id_fields = ("branch", "plan", "repo", "org", "org_instance", "current_rebuild")


@admin.register(BuildFlow)
class BuildFlowAdmin(admin.ModelAdmin):
    list_display = (
        "build",
        "status",
        "time_queue",
        "time_start",
        "time_end",
    )
    list_filter = ("build__repo", "build")


@admin.register(FlowTask)
class FlowTaskAdmin(admin.ModelAdmin):
    list_display = ("id", "build_flow", "stepnum", "path", "status")
    list_filter = ("build_flow__build__repo",)
    raw_id_fields = ["build_flow"]


@admin.register(Rebuild)
class RebuildAdmin(admin.ModelAdmin):
    list_display = (
        "build",
        "user",
        "status",
        "time_queue",
        "time_start",
        "time_end",
    )
    list_filter = ("build__repo", "build__plan")
    raw_id_fields = ("build", "org_instance")
