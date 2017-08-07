import os
import sys

import django
from django.views.generic.base import TemplateView
from pip.utils import get_installed_version


class AboutView(TemplateView):

    def get_context_data(self, **kwargs):
        context = super(AboutView, self).get_context_data(**kwargs)
        # django
        context['DJANGO_VERSION'] = '{}.{}.{}'.format(
            django.VERSION[0], # major
            django.VERSION[1], # minor
            django.VERSION[2], # micro
        )
        # python
        context['PYTHON_VERSION'] = '{}.{}.{}'.format(
            sys.version_info.major,
            sys.version_info.minor,
            sys.version_info.micro,
        )
        # heroku
        heroku_env_vars = [
            'HEROKU_APP_ID',
            'HEROKU_APP_NAME',
            'HEROKU_DYNO_ID',
            'HEROKU_RELEASE_CREATED_AT',
            'HEROKU_RELEASE_VERSION',
            'HEROKU_SLUG_COMMIT',
            'HEROKU_SLUG_DESCRIPTION',
        ]
        for var in heroku_env_vars:
            context[var] = os.environ.get(var,
                'Heroku dyno metadata not found')
        # cumulusci
        context['CUMULUSCI_VERSION'] = get_installed_version('cumulusci')
        return context
