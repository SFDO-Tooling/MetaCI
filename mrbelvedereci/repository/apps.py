from __future__ import unicode_literals

from django.apps import AppConfig


class RepositoryConfig(AppConfig):
    name = 'mrbelvedereci.repository'

    def ready(self):
        import mrbelvedereci.repository.handlers
