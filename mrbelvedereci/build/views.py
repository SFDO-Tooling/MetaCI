from datetime import datetime
from django.shortcuts import render
from django.http import HttpResponseRedirect
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404
from ansi2html import Ansi2HTMLConverter

from mrbelvedereci.build.models import Build
from mrbelvedereci.build.tasks import run_build
from mrbelvedereci.build.utils import view_queryset
from watson import search as watson

def build_list(request):
    builds = view_queryset(request)
    return render(request, 'build/build_list.html', context={'builds': builds})

def build_detail(request, build_id):
    build = get_object_or_404(Build, id = build_id)

    context = {
        'build': build,
        'flows': build.flows.order_by('time_queue'),
    }
    
    return render(request, 'build/build_detail.html', context=context)

def build_rebuild(request, build_id):
    build = get_object_or_404(Build, id = build_id)

    if not request.user.is_staff:
        return HttpResponseForbidden('You are not authorized to rebuild builds')
    
    build.status = 'queued'
    build.log += '\n=== Build restarted at {} by {} ===\n'.format(datetime.now(), request.user.username)
    build.save()

    run_build.delay(build.id)
   
    return HttpResponseRedirect('/builds/{}'.format(build.id)) 

def build_search(request):
    results = []

    q = request.GET.get('q')
    if q:
        results = watson.search(q)

    context = {
        'query': q,
        'search_entry_list': results,
    }

    return render(request, 'build/search.html', context=context)
    
