from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.http import HttpResponseRedirect
from django.shortcuts import render

from mrbelvedereci.notification.forms import AddBranchNotificationForm
from mrbelvedereci.notification.forms import AddPlanNotificationForm
from mrbelvedereci.notification.forms import AddRepositoryNotificationForm
from mrbelvedereci.notification.forms import DeleteNotificationForm
from mrbelvedereci.notification.models import BranchNotification
from mrbelvedereci.notification.models import PlanNotification
from mrbelvedereci.notification.models import RepositoryNotification


@login_required
def my_notifications(request):
    notifications = {
        'plan': request.user.plan_notifications.all(),
        'repo': request.user.repo_notifications.all(),
        'branch': request.user.branch_notifications.all(),
    }
    return render(
        request,
        'notification/my_notifications.html',
        context={'notifications': notifications},
    )


@login_required
def add_repository_notification(request):
    initial = {'user': request.user.id}
    if request.method == 'POST':
        form = AddRepositoryNotificationForm(request.POST, initial=initial)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect('/notifications')
    else:
        form = AddRepositoryNotificationForm(initial=initial)
    return render(
        request,
        'notification/add_repository_notification.html',
        context={'form': form},
    )


@login_required
def add_branch_notification(request):
    initial = {'user': request.user.id}
    if request.method == 'POST':
        form = AddBranchNotificationForm(request.POST, initial=initial)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect('/notifications')
    else:
        form = AddBranchNotificationForm(initial=initial)
    return render(
        request,
        'notification/add_branch_notification.html',
        context={'form': form},
    )


@login_required
def add_plan_notification(request):
    initial = {'user': request.user.id}
    if request.method == 'POST':
        form = AddPlanNotificationForm(request.POST, initial=initial)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect('/notifications')
    else:
        form = AddPlanNotificationForm(initial=initial)
    return render(
        request,
        'notification/add_plan_notification.html',
        context={'form': form},
    )


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
