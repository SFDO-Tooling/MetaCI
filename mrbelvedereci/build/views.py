from django.utils import timezone
from django.shortcuts import render
from django.http import Http404
from django.http import HttpResponseRedirect
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404
from ansi2html import Ansi2HTMLConverter

from mrbelvedereci.build.models import Build
from mrbelvedereci.build.models import Rebuild
from mrbelvedereci.build.tasks import run_build
from mrbelvedereci.build.utils import view_queryset
from watson import search as watson

def build_list(request):
    builds = view_queryset(request)
    return render(request, 'build/build_list.html', context={'builds': builds})

def build_detail(request, build_id, rebuild_id=None, tab=None):
    build = get_object_or_404(Build, id = build_id)
    rebuild = None

    if not request.user.is_staff:
        if build.plan.public:
            return HttpResponseForbidden('You are not authorized to view this build')
        if tab == 'org':
            return HttpResponseForbidden("You are not authorized to view this build's org info")

    if not rebuild_id:
        if build.current_rebuild:
            flows = build.current_rebuild.flows
        else:
            flows = build.flows
    else:
        if rebuild_id == 'original':
            flows = build.flows.filter(rebuild__isnull = True)
        else:
            rebuild = get_object_or_404(Rebuild, build_id = build.id, id=rebuild_id)
            flows = rebuild.flows

    flows = flows.order_by('time_queue')

    tests = {
        'total': 0,
        'pass': 0,
        'fail': 0,
        'failed_tests': [],
    }

    for flow in flows.all():
        if flow.tests_total:
            tests['total'] += flow.tests_total
        if flow.tests_pass:
            tests['pass'] += flow.tests_pass
        if flow.tests_fail:
            tests['fail'] += flow.tests_fail
            tests['failed_tests'].extend(list(flow.test_results.filter(outcome__in = ['Fail','CompileFail'])))
    
    context = {
        'build': build,
        'rebuild': rebuild,
        'original_build': rebuild_id == 'original',
        'tab': tab,
        'flows': flows,
        'tests': tests,
    }

    if not tab:
        return render(request, 'build/detail.html', context=context)
    elif tab == 'flows':
        return render(request, 'build/detail_flows.html', context=context)
    elif tab == 'tests':
        return render(request, 'build/detail_tests.html', context=context)
    elif tab == 'rebuilds':
        return render(request, 'build/detail_rebuilds.html', context=context)
    elif tab == 'org':
        return render(request, 'build/detail_org.html', context=context)

def build_rebuild(request, build_id):
    build = get_object_or_404(Build, id = build_id)

    if not request.user.is_staff:
        return HttpResponseForbidden('You are not authorized to rebuild builds')

    rebuild = Rebuild(
        build = build,
        user = request.user,
    )
    rebuild.save()
    
    build.status = 'queued'
    if not build.log:
        build.log = ''
    
    build.log += '\n=== Build restarted at {} by {} ===\n'.format(timezone.now(), request.user.username)
    build.current_rebuild = rebuild
    build.save()

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
    
