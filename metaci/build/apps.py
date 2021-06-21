from django.apps import AppConfig
from watson import search as watson


class BuildConfig(AppConfig):
    name = "metaci.build"

    def ready(self):
        import metaci.build.handlers  # noqa; side effect import

        Build = self.get_model("Build")
        BuildFlow = self.get_model("BuildFlow")
        watson.register(Build, exclude=["log"])
        watson.register(BuildFlow, exclude=["log"])
