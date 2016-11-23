from __future__ import unicode_literals

from django.apps import AppConfig


class GithubConfig(AppConfig):
    name = 'mrbelvedereci.github'

    def ready(self):
        import mrbelvedereci.github.handlers
