from django.contrib import admin
from mrbelvedereci.github.models import Branch
from mrbelvedereci.github.models import Repository

class BranchAdmin(admin.ModelAdmin):
    list_display = ('repo', 'name')
admin.site.register(Branch, BranchAdmin)

class RepositoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'owner')
admin.site.register(Repository, RepositoryAdmin)
