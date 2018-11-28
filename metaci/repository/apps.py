from __future__ import unicode_literals

from django.apps import AppConfig


class RepositoryConfig(AppConfig):
    name = "metaci.repository"

    def ready(self):
        import metaci.repository.handlers
