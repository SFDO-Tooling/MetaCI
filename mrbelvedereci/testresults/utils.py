from django.shortcuts import get_object_or_404
from mrbelvedereci.build.models import Build
from mrbelvedereci.build.models import BuildFlow


def find_buildflow(request, build_id, flow):
    build = get_object_or_404(Build, id=build_id)

    if not build.plan.public and not request.user.is_staff:
        raise Http404()
    query = {'build_id': build_id, 'flow': flow}
    if build.current_rebuild:
        query['rebuild_id'] = build.current_rebuild

    build_flow = get_object_or_404(BuildFlow, **query)
    return build_flow