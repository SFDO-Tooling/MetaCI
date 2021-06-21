from django.apps import AppConfig


class PlanConfig(AppConfig):
    name = "metaci.plan"

    def ready(self):
        import metaci.plan.handlers
