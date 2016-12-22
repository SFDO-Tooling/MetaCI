from django.core.paginator import EmptyPage
from django.core.paginator import PageNotAnInteger
from django.core.paginator import Paginator


def paginate(build_list, request):
    page = request.GET.get('page')
    per_page = request.GET.get('per_page', '25')
    paginator = Paginator(build_list, int(per_page))
    try:
        builds = paginator.page(page)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page.
        builds = paginator.page(1)
    except EmptyPage:
        # If page is out of range (e.g. 9999), deliver last page of results.
        builds = paginator.page(paginator.num_pages)
    return builds
