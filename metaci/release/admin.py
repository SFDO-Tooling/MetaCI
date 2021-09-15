from django.contrib import admin
from django.http import HttpResponseRedirect

from metaci.release.models import (
    ChangeCaseTemplate,
    ImplementationStep,
    Release,
    ReleaseCohort,
)
from metaci.release.utils import send_release_webhook, send_submit_webhook
from metaci.repository.models import Repository


class ImplementationStepInline(admin.TabularInline):
    model = ImplementationStep
    extra = 1


@admin.register(Release)
class ReleaseAdmin(admin.ModelAdmin):
    def get_form(self, request, obj=None, **kwargs):
        form = super(ReleaseAdmin, self).get_form(request, obj, **kwargs)
        repo_id = request.GET.get("repo_id")
        if repo_id is not None:
            repo = Repository.objects.get(pk=int(repo_id))
            form.base_fields["repo"].initial = repo
            next_version = None
            if repo.latest_release:
                if len(repo.latest_release.version_number.split(".")) > 1:
                    next_version = f"{repo.latest_release.version_number.split('.')[0]}.{int(repo.latest_release.version_number.split('.')[1]) + 1}"
            else:
                next_version = "1.0"
            if next_version is not None:
                form.base_fields["version_name"].initial = next_version
                form.base_fields["version_number"].initial = next_version
                form.base_fields[
                    "git_tag"
                ].initial = f"{repo.release_tag_regex}{next_version}"

        return form

    fieldsets = (
        (None, {"fields": ("repo", ("version_name", "version_number"), "status")}),
        (
            "Planning",
            {
                "fields": (
                    "release_creation_date",
                    ("sandbox_push_date", "production_push_date"),
                    "work_item_link",
                    "release_cohort",
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
            send_release_webhook(
                obj, obj.repo.orgs.get(name="packaging").configuration_item
            )
            self.message_user(request, "The change case has been successfully created.")
        if "_submit-change-case" in request.POST:
            send_submit_webhook(
                obj, obj.repo.orgs.get(name="packaging").configuration_item
            )
            self.message_user(
                request, "The change case has been successfully submitted."
            )
            return HttpResponseRedirect(".")
        return super().response_change(request, obj)


admin.site.register(ChangeCaseTemplate)
admin.site.register(ImplementationStep)
admin.site.register(ReleaseCohort)
