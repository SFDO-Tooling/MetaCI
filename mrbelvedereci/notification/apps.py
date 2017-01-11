from __future__ import unicode_literals

from django.apps import AppConfig


class NotificationConfig(AppConfig):
    name = 'mrbelvedereci.notification'

    def ready(self):
        import mrbelvedereci.notification.handlers
