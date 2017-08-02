from django.conf import settings
from django.views.generic.base import TemplateView


class AboutView(TemplateView):

    def get_context_data(self, **kwargs):
        context = super(AboutView, self).get_context_data(**kwargs)
        # try to add Heroku env vars
        heroku_env_vars = [
            'HEROKU_APP_ID',
            'HEROKU_APP_NAME',
            'HEROKU_DYNO_ID',
            'HEROKU_RELEASE_CREATED_AT',
            'HEROKU_RELEASE_VERSION',
            'HEROKU_SLUG_COMMIT',
            'HEROKU_SLUG_DESCRIPTION',
        ]
        default = 'Heroku dyno metadata not found'
        for var in heroku_env_vars:
            context[var] = getattr(settings, var, default)
        return context
