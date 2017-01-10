from django.contrib import admin
from mrbelvedereci.repository.models import Branch
from mrbelvedereci.repository.models import Repository

class BranchAdmin(admin.ModelAdmin):
    list_display = ('repo', 'name')
admin.site.register(Branch, BranchAdmin)

class RepositoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'owner')
admin.site.register(Repository, RepositoryAdmin)
