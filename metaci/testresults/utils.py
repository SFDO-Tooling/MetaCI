from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404
from metaci.build.models import Build
from metaci.build.models import BuildFlow


def find_buildflow(request, build_id, flow):
    """given a build_id and flow name, find a single BuildFlow (ala tests/ urls patterns)."""
    build = get_object_or_404(Build, id=build_id)

    if not request.user.has_perm("plan.view_builds", build.planrepo):
        raise PermissionDenied()
    query = {"build_id": build_id, "flow": flow}
    if build.current_rebuild:
        query["rebuild_id"] = build.current_rebuild

    build_flow = get_object_or_404(BuildFlow, **query)
    return build_flow
