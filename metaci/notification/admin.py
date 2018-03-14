from django.contrib import admin
from metaci.notification.models import RepositoryNotification
from metaci.notification.models import BranchNotification
from metaci.notification.models import PlanNotification
from metaci.notification.models import PlanRepositoryNotification

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

class PlanRepositoryNotificationAdmin(admin.ModelAdmin):
    list_display = ('planrepository', 'user')
    list_filter = ('planrepository__repo', 'user')
admin.site.register(PlanRepositoryNotification, PlanRepositoryNotificationAdmin)
