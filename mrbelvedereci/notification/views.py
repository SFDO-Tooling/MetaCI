from django.shortcuts import render
from django.http import HttpResponseForbidden
from django.http import HttpResponseRedirect
from django.contrib.auth.decorators import login_required

from mrbelvedereci.notification.forms import AddRepositoryNotificationForm
from mrbelvedereci.notification.forms import AddBranchNotificationForm
from mrbelvedereci.notification.forms import AddPlanNotificationForm
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

    context = {
        'notifications': notifications,
    }

    return render(request, 'notification/my_notifications.html', context=context)

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

    context = {
        'form': form,
    }

    return render(request, 'notification/add_repository_notification.html', context=context)

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

    context = {
        'form': form,
    }

    return render(request, 'notification/add_branch_notification.html', context=context)

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

    context = {
        'form': form,
    }

    return render(request, 'notification/add_plan_notification.html', context=context)

@login_required
def delete_branch_notification(request, pk):
    return delete_notification(request, BranchNotification.objects.get(pk=pk))

@login_required
def delete_plan_notification(request, pk):
    return delete_notification(request, PlanNotification.objects.get(pk=pk))

@login_required
def delete_repository_notification(request, pk):
    return delete_notification(request, RepositoryNotification.objects.get(pk=pk))

def delete_notification(request, o):
    if request.user != o.user:
        return HttpResponseForbidden()
    if request.method == 'POST':
        form = DeleteNotificationForm(request.POST)
        if form.is_valid():
            if request.POST['action'] == 'Delete':
                o.delete()
            return HttpResponseRedirect('/notifications')
    else:
        form = DeleteNotificationForm()
    return render(
        request,
        'notification/delete_notification.html',
        context={'form': form},
    )
