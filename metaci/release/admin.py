# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin

from metaci.release.models import Release


class ReleaseAdmin(admin.ModelAdmin):
    fieldsets = (
        (None, {"fields": ("repo", ("version_name", "version_number"), "status")}),
        (
            "Planning",
            {
                "fields": (
                    "release_creation_date",
                    ("sandbox_push_date", "production_push_date"),
                    "work_item_link",
                )
            },
        ),
        (
            "Source Control",
            {"fields": ("created_from_commit", "git_tag", "github_release")},
        ),
        ("Salesforce Release", {"fields": ("package_version_id", "trialforce_id")}),
    )

    list_display = (
        "repo",
        "version_name",
        "status",
        "release_creation_date",
        "package_version_id",
    )
    list_display_links = ("version_name",)
    list_filter = ("repo", "status")
    list_select_related = ("repo",)
    save_as = True
    search_fields = ["^package_version_id", "^git_tag"]
    empty_value_display = "-empty-"


admin.site.register(Release, ReleaseAdmin)
