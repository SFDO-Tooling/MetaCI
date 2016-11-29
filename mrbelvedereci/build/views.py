from django.shortcuts import render
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from ansi2html import Ansi2HTMLConverter

from mrbelvedereci.build.models import Build

def build_list(request):
    pass

def build_detail(request, build_id):
    build = get_object_or_404(Build, id = build_id)
    
    build_log = ''

    conv = Ansi2HTMLConverter()

    for flow in build.flows.all():
        if flow.log:
            build_log += conv.convert(flow.log)
    
    return HttpResponse(build_log)
