from django.contrib import admin
from django.http import HttpResponseRedirect
from metaci.release.models import ChangeCaseTemplate, ImplementationStep, Release
from metaci.release.utils import (
    send_release_webhook,
)


class ImplementationStepInline(admin.TabularInline):
    model = ImplementationStep
    extra = 1


@admin.register(Release)
class ReleaseAdmin(admin.ModelAdmin):
    # change_form_template = "templates/admin/release/release/change_form.html"
    fieldsets = (
        (None, {"fields": ("repo", ("version_name", "version_number"), "status")}),
        (
            "Planning",
            {
                "fields": (
                    "release_creation_date",
                    ("sandbox_push_date", "production_push_date"),
                    "work_item_link",
                    "change_case_template",
                    "change_case_link",
                )
            },
        ),
        (
            "Source Control",
            {"fields": ("created_from_commit", "git_tag", "github_release")},
        ),
        ("Salesforce Release", {"fields": ("package_version_id", "trialforce_id")}),
    )

    date_hierarchy = "release_creation_date"
    list_display = (
        "repo",
        "git_tag",
        "status",
        "release_creation_date",
        "package_version_id",
    )
    list_display_links = ("git_tag",)
    list_filter = ("repo", "status")
    list_select_related = ("repo",)
    search_fields = ["^package_version_id", "^git_tag"]
    empty_value_display = "-empty-"
    inlines = [ImplementationStepInline]

    def response_change(self, request, obj):
        if "_create-change-case" in request.POST:
            # matching_names_except_this = (
            #     self.get_queryset(request).filter(name=obj.name).exclude(pk=obj.id)
            # )
            # matching_names_except_this.delete()
            # obj.is_unique = True
            # obj.save()
            print("Here")
            breakpoint()
            send_release_webhook(obj, "NA.45")
            self.message_user(request, "The change case has been successfully created.")
            return HttpResponseRedirect(".")
        return super().response_change(request, obj)


admin.site.register(ChangeCaseTemplate)
admin.site.register(ImplementationStep)
