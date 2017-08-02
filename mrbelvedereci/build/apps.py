from __future__ import unicode_literals

from django.apps import AppConfig
from watson import search as watson


class BuildConfig(AppConfig):
    name = 'mrbelvedereci.build'

    def ready(self):
        import mrbelvedereci.build.handlers
        Build = self.get_model('Build')
        BuildFlow = self.get_model('BuildFlow')
        watson.register(Build)
        watson.register(BuildFlow)
