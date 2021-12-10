import json
from typing import Optional
from urllib.parse import urljoin

from django.conf import settings
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.exceptions import PermissionDenied
from django.http import Http404, HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.views.decorators.csrf import csrf_exempt

from metaci.build.utils import paginate, view_queryset
from metaci.cumulusci.forms import OrgLockForm, OrgUnlockForm
from metaci.cumulusci.models import Org, get_org_pool, PooledOrgRequest, ScratchOrgInstance
from metaci.cumulusci.tasks import org_claimed


@csrf_exempt
def request_pooled_org(request):
    # From the input, we need the cache key (the update_dependencies frozensteps)
    # and the org name, as well as the repo URL.
    # we transform the frozensteps into options that we can inject in a flow
    # and find a matching Org Pool instance, if any, with that cache key and repo URL

    # If no org pool matches, we'll return a 200 with an empty body.
    # Otherwise, we'll return the credentials for a prebuilt org
    # and delete the ScratchOrgInstance, and throw the org claimed signal.

    input_data = PooledOrgRequest(**json.loads(request.body))

    org_pool = get_org_pool(input_data)

    response_content = {}
    if org_pool and org_pool.pooled_orgs.count() > 0:
        returned_org = org_pool.pooled_orgs.first()
        response_content = returned_org.json
        returned_org.delete()

        org_claimed.send(sender=org_pool.__class__, org_pool=org_pool)
    return HttpResponse(
        content=json.dumps(response_content).encode("utf-8"),
        content_type="text/json",
        status=200,
    )


@login_required
def org_detail(request, org_id):
    org = Org.objects.get_for_user_or_404(request.user, {"id": org_id})

    # Get builds
    query = {"org": org}
    builds = view_queryset(request, query)

    # Get ScratchOrgInstances
    instances = org.instances.filter(deleted=False) if org.scratch else []

    context = {"builds": builds, "org": org, "instances": instances}
    context["can_log_in"] = org.scratch or settings.METACI_ALLOW_PERSISTENT_ORG_LOGIN
    return render(request, "cumulusci/org_detail.html", context=context)


# not wired to urlconf; called by org_lock and org_unlock


def _org_lock_unlock(request, org_id, action):
    org = get_object_or_404(Org, id=org_id)
    if org.scratch:
        raise PermissionDenied("Scratch orgs may not be locked/unlocked")
    if action == "lock":
        form_class = OrgLockForm
        template = "cumulusci/org_lock.html"
    elif action == "unlock":
        form_class = OrgUnlockForm
        template = "cumulusci/org_unlock.html"
    if request.method == "POST":
        form = form_class(request.POST)
        if form.is_valid():
            if request.POST["action"] == "Lock":
                org.lock()
            elif request.POST["action"] == "Unlock":
                org.unlock()
            return HttpResponseRedirect(org.get_absolute_url())
    else:
        form = form_class()
    return render(request, template, context={"form": form, "org": org})


@user_passes_test(lambda u: u.is_superuser)
def org_lock(request, org_id):
    return _org_lock_unlock(request, org_id, "lock")


@user_passes_test(lambda u: u.is_superuser)
def org_unlock(request, org_id):
    return _org_lock_unlock(request, org_id, "unlock")


@login_required
def org_login(request, org_id, instance_id=None):
    org = Org.objects.get_for_user_or_404(request.user, {"id": org_id})

    def get_org_config(org):
        org_config = org.get_org_config()
        org_config.refresh_oauth_token(keychain=None)
        return org_config

    # For non-scratch orgs, just log into the org
    if not org.scratch:
        if not settings.METACI_ALLOW_PERSISTENT_ORG_LOGIN:
            raise PermissionDenied("Logging in to persistent orgs is disabled.")

        org_config = get_org_config(org)
        return HttpResponseRedirect(org_config.start_url)

    # If an instance was selected, log into the org
    if instance_id:
        instance = get_object_or_404(ScratchOrgInstance, org_id=org_id, id=instance_id)

        # If the org is deleted, render the org deleted template
        if instance.deleted:
            raise Http404("Cannot log in: the org instance is already deleted")

        # Log into the scratch org
        session = instance.get_jwt_based_session()
        return HttpResponseRedirect(
            urljoin(
                str(session["instance_url"]),
                f"secur/frontdoor.jsp?sid={session['access_token']}",
            )
        )

    raise Http404()


@login_required
def org_instance_delete(request, org_id, instance_id):
    instance = get_object_or_404(ScratchOrgInstance, org_id=org_id, id=instance_id)

    # Verify access
    try:
        Org.objects.for_user(request.user).get(id=org_id)
    except Org.DoesNotExist:
        raise PermissionDenied("You are not authorized to view this org")

    if instance.deleted:
        raise Http404("Cannot delete: this org instance is already deleted")

    instance.delete_org()
    return HttpResponseRedirect(instance.get_absolute_url())


@login_required
def org_instance_detail(request, org_id, instance_id):
    instance = get_object_or_404(ScratchOrgInstance, org_id=org_id, id=instance_id)

    # Verify access
    try:
        Org.objects.for_user(request.user).get(id=org_id)
    except Org.DoesNotExist:
        raise PermissionDenied("You are not authorized to view this org")

    # Get builds
    query = {"org_instance": instance}
    builds = view_queryset(request, query)

    context = {"builds": builds, "instance": instance}
    return render(request, "cumulusci/org_instance_detail.html", context=context)


@login_required
def org_list(request):
    query = {}
    repo = request.GET.get("repo")
    if repo:
        query["repo__name"] = repo
    scratch = request.GET.get("scratch")
    if scratch:
        query["scratch"] = scratch

    orgs = Org.objects.for_user(request.user).filter(**query)
    orgs = orgs.order_by("id")

    orgs = paginate(orgs, request)
    context = {"orgs": orgs}
    return render(request, "cumulusci/org_list.html", context=context)
