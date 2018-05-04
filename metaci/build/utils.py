import os
import subprocess

from ansi2html import Ansi2HTMLConverter
from cumulusci.core.exceptions import CommandException
from django.apps import apps
from django.core.paginator import EmptyPage
from django.core.paginator import PageNotAnInteger
from django.core.paginator import Paginator
from django.db.models import Q


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


def set_build_info(build, **kwargs):
    for attr, value in kwargs.items():
        setattr(build, attr, value)
    build.save()


def view_queryset(request, query=None, status=None, filter_class=None):
    if not query:
        query = {}

    if not request.user.is_staff:
        query['plan__public'] = True
        query['repo__public'] = True

    Build = apps.get_model('build', 'Build')
    builds = Build.objects.all()
    if query:
        builds = builds.filter(**query)
    if status:
        builds = builds.filter(
            Q(
                current_rebuild__isnull=True,
                status=status,
            ) | Q(
                current_rebuild__isnull=False,
                current_rebuild__status=status,
            ),
        )

    order_by = request.GET.get('order_by', '-time_queue')
    order_by = order_by.split(',')
    builds = builds.order_by(*order_by)

    if filter_class:
        build_filter = filter_class(request.GET, builds)
        paginated = paginate(build_filter.qs, request)
        return build_filter, paginated
    else:
        builds = paginate(builds, request)
        return builds


def format_log(log):
    conv = Ansi2HTMLConverter(dark_bg=False, scheme='solarized', markup_lines=True)
    headers = conv.produce_headers()
    content = conv.convert(log, full=False)
    content = '<pre class="ansi2html-content">{}</pre>'.format(
        content.encode('utf8'))
    # content = '<div class="body_foreground body_background">{}</div>'.format(
    #    content)
    return headers + content

def run_command(command, env=None, cwd=None):
    kwargs = {}
    if env:
        kwargs['env'] = env
    if cwd:
        kwargs['cwd'] = cwd
    p = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        bufsize=1,
        shell=True,
        executable='/bin/bash',
        **kwargs
    )
    for line in iter(p.stdout.readline, ''):
        yield line
    p.stdout.close()
    p.wait()
    if p.returncode:
        message = 'Return code: {}\nstderr: {}'.format(
            p.returncode,
            p.stderr,
        )
        raise CommandException(message)
