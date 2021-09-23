from django.core.exceptions import PermissionDenied
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required

from metaci.release.models import ReleaseCohort, Release

def cohort_list(request):
    if not can_view_cohorts(request.user):
        raise PermissionDenied('You are not authorized to view this page.')
    cohorts = ReleaseCohort.objects.all()
    context = {'cohorts': cohorts}
    return render(request, "cohort/list.html", context=context)

def cohort_detail(request, cohort_id):
    if not can_view_cohorts(request.user):
        raise PermissionDenied('You are not authorized to view this page.')
    cohort = get_object_or_404(ReleaseCohort, id=cohort_id)
    releases = list(Release.objects.filter(release_cohort=cohort.id))
    context = {'cohort': cohort, 'releases': releases}
    return render(request, "cohort/detail.html", context=context)


def can_view_cohorts(user):
    """To access Cohort views user need to be
    authenticated and either be an admin, or
    in a group that has the 'view cohorts' permission."""
    return user.is_authenticated and user.has_perm('release.view_releasecohort')
