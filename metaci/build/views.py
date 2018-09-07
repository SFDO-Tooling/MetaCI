from ansi2html import Ansi2HTMLConverter
from django.db import transaction
from django.http import Http404
from django.http import HttpResponseForbidden
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.shortcuts import render
from django.utils import timezone
from watson import search as watson

from metaci.build.exceptions import BuildError
from metaci.build.filters import BuildFilter
from metaci.build.forms import QATestingForm
from metaci.build.models import Build
from metaci.build.models import Rebuild
from metaci.build.tasks import run_build
from metaci.build.utils import view_queryset


def build_list(request):
    query = {}
    repo = request.GET.get('repo')
    if repo:
        query['repo__name'] = repo
    build_filter, builds = view_queryset(request, query, request.GET.get('status'), filter_class=BuildFilter)
    context = {
        'filter': build_filter,
        'builds': builds,
    }
    return render(request, 'build/build_list.html', context=context)

@transaction.non_atomic_requests
def build_detail(request, build_id, rebuild_id=None, tab=None):
    build = get_object_or_404(Build, id=build_id)
    rebuild = None

    if not request.user.is_staff:
        if not build.plan.public:
            return HttpResponseForbidden(
                'You are not authorized to view this build')
        if tab == 'org':
            return HttpResponseForbidden(
                "You are not authorized to view this build's org info")
        if tab == 'qa':
            return HttpResponseForbidden(
                "You are not authorized to view this build's QA info")

    if not rebuild_id:
        if build.current_rebuild:
            flows = build.current_rebuild.flows
        else:
            flows = build.flows
    else:
        if rebuild_id == 'original':
            flows = build.flows.filter(rebuild__isnull=True)
        else:
            rebuild = get_object_or_404(Rebuild, build_id=build.id,
                                        id=rebuild_id)
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
            tests['failed_tests'].extend(list(flow.test_results.filter(
                outcome__in=['Fail', 'CompileFail'])))

    if rebuild and rebuild.org_instance:
        org_instance = rebuild.org_instance
    else:
        org_instance = build.org_instance
    context = {
        'build': build,
        'rebuild': rebuild,
        'original_build': rebuild_id == 'original',
        'tab': tab,
        'flows': flows,
        'tests': tests,
        'org_instance': org_instance,
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
    elif tab == 'qa':
        if request.method == 'POST':
            form = QATestingForm(build, request.user, request.POST)
            if form.is_valid():
                form.save()
                build = Build.objects.get(id=build.id)
                context['build'] = build
        else:
            form = QATestingForm(build, request.user)
        context['form'] = form
        return render(request, 'build/detail_qa.html', context=context)
    else:
        raise BuildError('Unsupported value for "tab": {}'.format(tab))


def build_rebuild(request, build_id):
    build = get_object_or_404(Build, id=build_id)

    if not request.user.is_staff:
        return HttpResponseForbidden(
            'You are not authorized to rebuild builds')

    rebuild = Rebuild(
        build=build,
        user=request.user,
        status='queued',
    )
    rebuild.save()

    if not build.log:
        build.log = ''

    build.log += '\n=== Build restarted at {} by {} ===\n'.format(
        timezone.now(), request.user.username)
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
