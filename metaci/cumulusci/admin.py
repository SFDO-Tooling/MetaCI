from django.contrib import admin
from metaci.cumulusci.models import Org
from metaci.cumulusci.models import ScratchOrgInstance
from metaci.cumulusci.models import Service


class OrgAdmin(admin.ModelAdmin):
    list_display = ('name', 'repo', 'scratch')
    list_filter = ('name', 'scratch', 'repo')
admin.site.register(Org, OrgAdmin)


class ServiceAdmin(admin.ModelAdmin):
    list_display = ('name',)
admin.site.register(Service, ServiceAdmin)


class ScratchOrgInstanceAdmin(admin.ModelAdmin):
    list_display = ('org', 'build', 'sf_org_id', 'username', 'deleted', 'time_created', 'time_deleted')
    list_filter = ('deleted', 'org')
admin.site.register(ScratchOrgInstance, ScratchOrgInstanceAdmin)
