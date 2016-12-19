from django.shortcuts import render
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from ansi2html import Ansi2HTMLConverter

from mrbelvedereci.build.models import Build
from mrbelvedereci.build.tasks import run_build

def build_list(request):
    builds = Build.objects.all()
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

    run_build.apply_async((build.id,), countdown=1)
   
    return HttpResponseRedirect('/builds/{}'.format(build.id)) 
