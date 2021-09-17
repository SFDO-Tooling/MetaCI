from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required

from metaci.release.models import ReleaseCohort, Release

@login_required
def cohort_list(request):
    # TODO: check if user has view cohort perms
    cohorts = ReleaseCohort.objects.all()
    context = {'cohorts': cohorts}
    return render(request, "cohort/list.html", context=context)

@login_required
def cohort_detail(request, cohort_id):
    # TODO: check if user has view cohort perms
    cohort = get_object_or_404(ReleaseCohort, id=cohort_id)
    releases = list(Release.objects.filter(release_cohort=cohort.id))
    print(f'>>> releases: {releases}')
    print(f'release repo: {releases[0].repo}')
    print(f'release version num: {releases[0].version_number}')
    print(f'>>> num releases: {len(releases)}')
    print(f'>>> cohort: {cohort}')
    context = {'cohort': cohort, 'releases': releases}
    return render(request, "cohort/detail.html", context=context)
