from __future__ import unicode_literals

from django.apps import AppConfig

class TriggerConfig(AppConfig):
    name = 'mrbelvedereci.trigger'

    def ready(self):
        import mrbelvedereci.trigger.handlers
