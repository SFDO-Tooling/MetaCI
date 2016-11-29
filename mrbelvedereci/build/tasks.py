from celery import shared_task
from mrbelvedereci.build.models import Build

@shared_task
def run_build(build_id):
    build = Build.objects.get(id=build_id)
    build.run()
    return build.status
