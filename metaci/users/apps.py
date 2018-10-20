from django.apps import AppConfig


class UsersConfig(AppConfig):
    name = 'metaci.users'
    verbose_name = "Users"

    def ready(self):
        import metaci.users.handlers
