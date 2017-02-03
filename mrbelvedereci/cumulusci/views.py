from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.http import Http404
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.shortcuts import get_object_or_404

from mrbelvedereci.build.utils import view_queryset
from mrbelvedereci.cumulusci.models import Org
from mrbelvedereci.cumulusci.models import ScratchOrgInstance

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
    
@staff_member_required
def org_login(request, org_id, instance_id=None):
    org = get_object_or_404(Org, id=org_id)

    # For non-scratch orgs, just log into the org
    if not org.scratch:
        org_config = org.get_org_config()
        return HttpResponseRedirect(org_config.start_url)

    # If an instance was selected, log into the org
    if instance_id:
        instance = get_object_or_404(ScratchOrgInstance, org_id=org_id, id=instance_id)

        # If the org is deleted, render the org deleted template
        if instance.deleted:
            raise Http404("Cannot log in: the org instance is already deleted")

        # Log into the scratch org
        org_config = instance.get_org_config()
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
    except:
        return render(request, 'cumulusci/org_delete_failed.html', context=context)
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
