from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.forms import modelform_factory
from django.shortcuts import render
from django.views.generic import CreateView, DeleteView

from metaci.notification.forms import AddNotificationForm
from metaci.notification.models import (
    BranchNotification,
    PlanNotification,
    PlanRepositoryNotification,
    RepositoryNotification,
)


@login_required
def my_notifications(request):
    notifications = {
        "plan": request.user.plan_notifications.all(),
        "planrepository": request.user.planrepository_notifications.all(),
        "repo": request.user.repo_notifications.all(),
        "branch": request.user.branch_notifications.all(),
    }
    return render(
        request,
        "notification/my_notifications.html",
        context={"notifications": notifications},
    )


class NotificationViewMixin(LoginRequiredMixin):
    success_url = "/notifications"
    context_object_name = "notification"

    def get_context_data(self, **kwargs):
        context = super(NotificationViewMixin, self).get_context_data(**kwargs)
        # populate notification_type for template w/ model verbose name
        context["notification_type"] = self.model._meta.verbose_name.title()
        return context


class AddNotificationBaseView(NotificationViewMixin, CreateView):
    template_name = "notification/add_notification.html"

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super(AddNotificationBaseView, self).form_valid(form)

    def get_form_class(self):
        return modelform_factory(self.model, form=AddNotificationForm)


class DeleteNotificationBaseView(NotificationViewMixin, DeleteView):
    template_name = "notification/delete_notification.html"

    def get_queryset(self):
        qs = super(DeleteNotificationBaseView, self).get_queryset()
        return qs.filter(user=self.request.user)


class AddPlanRepositoryNotification(AddNotificationBaseView):
    model = PlanRepositoryNotification


class AddPlanNotification(AddNotificationBaseView):
    model = PlanNotification


class AddRepositoryNotification(AddNotificationBaseView):
    model = RepositoryNotification


class AddBranchNotification(AddNotificationBaseView):
    model = BranchNotification


class DeletePlanRepositoryNotification(DeleteNotificationBaseView):
    model = PlanRepositoryNotification


class DeletePlanNotification(DeleteNotificationBaseView):
    model = PlanNotification


class DeleteRepositoryNotification(DeleteNotificationBaseView):
    model = RepositoryNotification


class DeleteBranchNotification(DeleteNotificationBaseView):
    model = BranchNotification
