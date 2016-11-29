from django.contrib import admin
from mrbelvedereci.salesforce.models import Org

class OrgAdmin(admin.ModelAdmin):
    list_display = ('name','repo','scratch')
    list_filter = ('repo','scratch')
admin.site.register(Org, OrgAdmin)
