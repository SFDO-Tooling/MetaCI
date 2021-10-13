from django.core.exceptions import PermissionDenied
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils import timezone

from metaci.release.models import ReleaseCohort, Release


def cohort_list(request):
    if not can_view_cohorts(request.user):
        raise PermissionDenied("You are not authorized to view this page.")
    cohorts = ReleaseCohort.objects.all()
    context = {"cohorts": cohorts}
    return render(request, "cohort/list.html", context=context)


def cohort_detail(request, cohort_id):
    if not can_view_cohorts(request.user):
        raise PermissionDenied("You are not authorized to view this page.")
    cohort = get_object_or_404(ReleaseCohort, id=cohort_id)
    releases = list(Release.objects.filter(release_cohort=cohort.id))

    merge_freeze_active = is_merge_freeze_active(cohort)
    context = {
        "cohort": cohort,
        "releases": releases,
        "merge_freeze_active": merge_freeze_active,
    }
    return render(request, "cohort/detail.html", context=context)


def is_merge_freeze_active(cohort: ReleaseCohort) -> bool:
    return (
        cohort.merge_freeze_start < timezone.now() < cohort.merge_freeze_end
    )


def can_view_cohorts(user):
    """To access Cohort views user need to be
    authenticated and either be an admin, or
    in a group that has the 'view cohorts' permission."""
    return user.is_authenticated and user.has_perm("release.view_releasecohort")
