from __future__ import unicode_literals

from django.apps import AppConfig


class NotificationConfig(AppConfig):
    name = "metaci.notification"

    def ready(self):
        import metaci.notification.handlers
