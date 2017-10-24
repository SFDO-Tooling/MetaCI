from django.contrib import admin
from mrbelvedereci.notification.models import RepositoryNotification
from mrbelvedereci.notification.models import BranchNotification
from mrbelvedereci.notification.models import PlanNotification

class RepositoryNotificationAdmin(admin.ModelAdmin):
    list_display = ('repo', 'user')
    list_filter = ('repo', 'user')
admin.site.register(RepositoryNotification, RepositoryNotificationAdmin)

class BranchNotificationAdmin(admin.ModelAdmin):
    list_display = ('branch', 'user')
    list_filter = ('branch__repo', 'user')
admin.site.register(BranchNotification, BranchNotificationAdmin)

class PlanNotificationAdmin(admin.ModelAdmin):
    list_display = ('plan', 'user')
    list_filter = ('plan__repos', 'user')
admin.site.register(PlanNotification, PlanNotificationAdmin)
