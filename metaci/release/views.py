from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required

from metaci.release.models import ReleaseCohort

@login_required
def cohort_list(request):
    cohorts = ReleaseCohort.objects.all()
    context = {'cohorts': cohorts}
    return render(request, "cohort/list.html", context=context)

@login_required
def cohort_detail(request, cohort_id):
    cohort = get_object_or_404(ReleaseCohort, id=cohort_id)
    context = {'cohort': cohort}
    return render(request, "cohort/detail.html", context=context)
