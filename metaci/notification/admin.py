from django.contrib import admin
from metaci.notification.models import RepositoryNotification
from metaci.notification.models import BranchNotification
from metaci.notification.models import PlanNotification
from metaci.notification.models import PlanRepositoryNotification

class RepositoryNotificationAdmin(admin.ModelAdmin):
    list_display = ('target', 'user')
    list_filter = ('target', 'user')
admin.site.register(RepositoryNotification, RepositoryNotificationAdmin)

class BranchNotificationAdmin(admin.ModelAdmin):
    list_display = ('target', 'user')
    list_filter = ('target__repo', 'user')
admin.site.register(BranchNotification, BranchNotificationAdmin)

class PlanNotificationAdmin(admin.ModelAdmin):
    list_display = ('target', 'user')
    list_filter = ('target__repos', 'user')
admin.site.register(PlanNotification, PlanNotificationAdmin)

class PlanRepositoryNotificationAdmin(admin.ModelAdmin):
    list_display = ('target', 'user')
    list_filter = ('target__repo', 'user')
admin.site.register(PlanRepositoryNotification, PlanRepositoryNotificationAdmin)
