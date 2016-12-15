from django.contrib import admin
from mrbelvedereci.cumulusci.models import Org
from mrbelvedereci.cumulusci.models import Service

class OrgAdmin(admin.ModelAdmin):
    list_display = ('name','repo','scratch')
    list_filter = ('repo','scratch')
admin.site.register(Org, OrgAdmin)

class ServiceAdmin(admin.ModelAdmin):
    list_display = ('name',)
admin.site.register(Service, ServiceAdmin)
