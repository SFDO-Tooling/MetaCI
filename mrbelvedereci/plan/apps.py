from __future__ import unicode_literals

from django.apps import AppConfig

class PlanConfig(AppConfig):
    name = 'mrbelvedereci.plan'

    def ready(self):
        import mrbelvedereci.plan.handlers
