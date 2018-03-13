from __future__ import unicode_literals

from django.db import models

# Create your models here.
class PlanNotification(models.Model):
    user = models.ForeignKey('users.User', related_name='plan_notifications', on_delete=models.CASCADE)
    plan = models.ForeignKey('plan.Plan', related_name='notifications', on_delete=models.CASCADE)
    on_success = models.BooleanField(default=False)
    on_fail = models.BooleanField(default=True)
    on_error = models.BooleanField(default=True)

class PlanRepositoryNotification(models.Model):
    user = models.ForeignKey('users.User', related_name='planrepository_notifications')
    planrepository = models.ForeignKey('plan.PlanRepository', related_name='notifications')
    on_success = models.BooleanField(default=False)
    on_fail = models.BooleanField(default=True)
    on_error = models.BooleanField(default=True)

class BranchNotification(models.Model):
    user = models.ForeignKey('users.User', related_name='branch_notifications', on_delete=models.CASCADE)
    branch = models.ForeignKey('repository.Branch', related_name='notifications', on_delete=models.CASCADE)
    on_success = models.BooleanField(default=False)
    on_fail = models.BooleanField(default=True)
    on_error = models.BooleanField(default=True)

class RepositoryNotification(models.Model):
    user = models.ForeignKey('users.User', related_name='repo_notifications', on_delete=models.CASCADE)
    repo = models.ForeignKey('repository.Repository', related_name='notifications', on_delete=models.CASCADE)
    on_success = models.BooleanField(default=False)
    on_fail = models.BooleanField(default=True)
    on_error = models.BooleanField(default=True)
