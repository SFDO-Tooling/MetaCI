from __future__ import unicode_literals

from django.apps import AppConfig


class BuildConfig(AppConfig):
    name = 'mrbelvedereci.build'

    def ready(self):
        import mrbelvedereci.build.handlers
