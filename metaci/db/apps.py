from django.apps import AppConfig


class DBUtils(AppConfig):
    name = "metaci.db"

    def ready(self):
        pass
