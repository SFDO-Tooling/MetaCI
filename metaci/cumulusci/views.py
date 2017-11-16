from django.contrib.auth.decorators import login_required
from django.contrib.auth.decorators import user_passes_test
from django.contrib.admin.views.decorators import staff_member_required
from django.http import Http404
from django.http import HttpResponseForbidden
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.shortcuts import get_object_or_404

from metaci.build.utils import paginate
from metaci.build.utils import view_queryset
from metaci.cumulusci.forms import OrgLockForm
from metaci.cumulusci.forms import OrgUnlockForm
from metaci.cumulusci.models import Org
from metaci.cumulusci import choices
from metaci.cumulusci.models import ScratchOrgInstance
from metaci.cumulusci.utils import get_connected_app


@staff_member_required
def org_detail(request, org_id):
    org = get_object_or_404(Org, id=org_id)
    query = {'org': org}
    builds = view_queryset(request, query)
    instances = org.instances.filter(deleted=False)

    context = {
        'builds': builds,
        'org': org,
        'instances': instances,
    }
    return render(request, 'cumulusci/org_detail.html', context=context)

# not wired to urlconf; called by org_lock and org_unlock


def _org_lock_unlock(request, org_id, action):
    org = get_object_or_404(Org, id=org_id)
    if org.scratch:
        raise HttpResponseForbidden('Scratch orgs may not be locked/unlocked')
    if action == 'lock':
        form_class = OrgLockForm
        template = 'cumulusci/org_lock.html'
    elif action == 'unlock':
        form_class = OrgUnlockForm
        template = 'cumulusci/org_unlock.html'
    if request.method == 'POST':
        form = form_class(request.POST)
        if form.is_valid():
            if request.POST['action'] == 'Lock':
                org.lock()
            elif request.POST['action'] == 'Unlock':
                org.unlock()
            return HttpResponseRedirect(org.get_absolute_url())
    else:
        form = form_class()
    return render(request, template, context={'form': form, 'org': org})


@user_passes_test(lambda u: u.is_superuser)
def org_lock(request, org_id):
    return _org_lock_unlock(request, org_id, 'lock')


@user_passes_test(lambda u: u.is_superuser)
def org_unlock(request, org_id):
    return _org_lock_unlock(request, org_id, 'unlock')


@staff_member_required
def org_login(request, org_id, instance_id=None):
    org = get_object_or_404(Org, id=org_id)

    def get_org_config(org):
        org_config = org.get_org_config()
        connected_app = get_connected_app()
        org_config.refresh_oauth_token(connected_app)
        return org_config

    # For non-scratch orgs, just log into the org
    if not org.scratch:
        org_config = get_org_config(org)
        return HttpResponseRedirect(org_config.start_url)

    # If an instance was selected, log into the org
    if instance_id:
        instance = get_object_or_404(ScratchOrgInstance, org_id=org_id, id=instance_id)

        # If the org is deleted, render the org deleted template
        if instance.deleted:
            raise Http404("Cannot log in: the org instance is already deleted")

        # Log into the scratch org
        org_config = get_org_config(instance)
        return HttpResponseRedirect(org_config.start_url)

    raise Http404()


@staff_member_required
def org_instance_delete(request, org_id, instance_id):
    instance = get_object_or_404(ScratchOrgInstance, org_id=org_id, id=instance_id)

    context = {
        'instance': instance,
    }
    if instance.deleted:
        raise Http404("Cannot delete: this org instance is already deleted")

    try:
        instance.delete_org()
    except Exception as e:
        pass
    return HttpResponseRedirect(instance.get_absolute_url())


@staff_member_required
def org_instance_detail(request, org_id, instance_id):
    instance = get_object_or_404(ScratchOrgInstance, org_id=org_id, id=instance_id)
    query = {'org_instance': instance}
    builds = view_queryset(request, query)

    context = {
        'builds': builds,
        'instance': instance,
    }
    return render(request, 'cumulusci/org_instance_detail.html', context=context)

@staff_member_required
def org_list(request):
    query = {}
    repo = request.GET.get('repo')
    if repo:
        query['repo__name'] = repo
    scratch = request.GET.get('scratch')
    if scratch:
        query['scratch'] = scratch
    org_type = request.GET.get('org_type')
    if org_type:
        query['org_type'] = org_type
    query['supertype'] = request.GET.get('supertype', choices.SUPERTYPE_CI)
    orgs = Org.objects.filter(**query)
    orgs = orgs.order_by('id')
    orgs = paginate(orgs, request)
    context = {'orgs': orgs}
    return render(request, 'cumulusci/org_list.html', context=context)
