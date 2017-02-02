from django.core.paginator import EmptyPage
from django.core.paginator import PageNotAnInteger
from django.core.paginator import Paginator
from mrbelvedereci.build.models import Build

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

def view_queryset(request, query=None):
    if not query:
        query = {}

    if not request.user.is_staff:
        query['plan__public'] = True

    builds = Build.objects.all()
    if query:
        builds = builds.filter(**query)

    order_by = request.GET.get('order_by', '-time_queue')
    order_by = order_by.split(',')
    builds = builds.order_by(*order_by)

    builds = paginate(builds, request)
    return builds
