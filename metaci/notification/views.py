from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.views.generic import CreateView
from django.forms import modelform_factory

from metaci.notification.forms import DeleteNotificationForm
from metaci.notification.forms import AddNotificationForm
from metaci.notification.models import BranchNotification
from metaci.notification.models import PlanNotification
from metaci.notification.models import PlanRepositoryNotification
from metaci.notification.models import RepositoryNotification


@login_required
def my_notifications(request):
    notifications = {
        'plan': request.user.plan_notifications.all(),
        'planrepository': request.user.planrepository_notifications.all(),
        'repo': request.user.repo_notifications.all(),
        'branch': request.user.branch_notifications.all(),
    }
    return render(
        request,
        'notification/my_notifications.html',
        context={'notifications': notifications},
    )

class AddNotificationBaseView(CreateView):
    # subviews will define a Model
    # it should create a generic add notification form
    # it should render the add_notification.html template
    # it requires login access
    template_name = 'notification/add_notification.html'
    success_url = '/notifications'
    
    def get_form_class(self):
        return modelform_factory(self.model, form=AddNotificationForm)

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super(AddNotificationBaseView, self).form_valid(form)

    def get_context_data(self, **kwargs):
        context = super(AddNotificationBaseView, self).get_context_data(**kwargs)
        # populate notification_type for template w/ model verbose name
        context['notification_type'] = self.model._meta.verbose_name.title()
        return context


class AddPlanRepositoryNotification(AddNotificationBaseView):
    model = PlanRepositoryNotification

class AddPlanNotification(AddNotificationBaseView):
    model = PlanNotification

class AddRepositoryNotification(AddNotificationBaseView):
    model = RepositoryNotification

class AddBranchNotification(AddNotificationBaseView):
    model = BranchNotification


@login_required
def delete_branch_notification(request, pk):
    return _delete_notification(
        request,
        BranchNotification.objects.get(pk=pk),
    )


@login_required
def delete_plan_notification(request, pk):
    return _delete_notification(
        request,
        PlanNotification.objects.get(pk=pk),
    )


@login_required
def delete_planrepository_notification(request, pk):
    return _delete_notification(
        request,
        PlanRepositoryNotification.objects.get(pk=pk),
    )


@login_required
def delete_repository_notification(request, pk):
    return _delete_notification(
        request,
        RepositoryNotification.objects.get(pk=pk),
    )

# not wired to urlconf; called by delete_*_notification functions
def _delete_notification(request, notification):
    if request.user != notification.user:
        return HttpResponseForbidden()
    if request.method == 'POST':
        form = DeleteNotificationForm(request.POST)
        if form.is_valid():
            if request.POST['action'] == 'Delete':
                notification.delete()
            return HttpResponseRedirect('/notifications')
    else:
        form = DeleteNotificationForm()
    return render(
        request,
        'notification/delete_notification.html',
        context={
            'form': form,
            'notification': notification,
            'notification_type': notification.__class__.__name__.replace(
                'Notification',
                '',
            ),
        },
    )
