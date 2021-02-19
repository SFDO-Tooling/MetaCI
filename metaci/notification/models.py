from django.db import models


class AbstractNotification(models.Model):
    on_success = models.BooleanField(default=False)
    on_fail = models.BooleanField(default=True)
    on_error = models.BooleanField(default=True)

    class Meta:
        abstract = True


class PlanNotification(AbstractNotification):
    user = models.ForeignKey(
        "users.User", related_name="plan_notifications", on_delete=models.CASCADE
    )
    target = models.ForeignKey(
        "plan.Plan",
        related_name="notifications",
        on_delete=models.CASCADE,
        db_column="plan_id",
        verbose_name="plan",
    )


class PlanRepositoryNotification(AbstractNotification):
    user = models.ForeignKey(
        "users.User",
        related_name="planrepository_notifications",
        on_delete=models.CASCADE,
    )
    target = models.ForeignKey(
        "plan.PlanRepository",
        related_name="notifications",
        db_column="planrepository_id",
        verbose_name="planrepository",
        on_delete=models.CASCADE,
    )


class BranchNotification(AbstractNotification):
    user = models.ForeignKey(
        "users.User", related_name="branch_notifications", on_delete=models.CASCADE
    )
    target = models.ForeignKey(
        "repository.Branch",
        related_name="notifications",
        on_delete=models.CASCADE,
        db_column="branch_id",
        verbose_name="branch",
    )


class RepositoryNotification(AbstractNotification):
    user = models.ForeignKey(
        "users.User", related_name="repo_notifications", on_delete=models.CASCADE
    )
    target = models.ForeignKey(
        "repository.Repository",
        related_name="notifications",
        on_delete=models.CASCADE,
        db_column="repo_id",
        verbose_name="repo",
    )
