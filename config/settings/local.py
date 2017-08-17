# -*- coding: utf-8 -*-
"""
Local settings

- Run in Debug mode

- Use console backend for emails

- Add Django Debug Toolbar
- Add django-extensions as app
"""

import socket
import os
from .common import *  # noqa

# DEBUG
# ------------------------------------------------------------------------------
DEBUG = env.bool('DJANGO_DEBUG', default=True)
TEMPLATES[0]['OPTIONS']['debug'] = DEBUG

# SECRET CONFIGURATION
# ------------------------------------------------------------------------------
# See: https://docs.djangoproject.com/en/dev/ref/settings/#secret-key
# Note: This key only used for development and testing.
SECRET_KEY = env('DJANGO_SECRET_KEY', default='!)_b4xaov6!0b^_=96*wh@p-9si4p0ho-@4&g7eija9gaxhmo!')

# Mail settings
# ------------------------------------------------------------------------------

EMAIL_PORT = 1025

EMAIL_HOST = 'localhost'
EMAIL_BACKEND = env('DJANGO_EMAIL_BACKEND',
                    default='django.core.mail.backends.console.EmailBackend')


# CACHING
# ------------------------------------------------------------------------------
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': ''
    }
}

# django-debug-toolbar
# ------------------------------------------------------------------------------
MIDDLEWARE += ('debug_toolbar.middleware.DebugToolbarMiddleware',)
INSTALLED_APPS += ('debug_toolbar', )

INTERNAL_IPS = ['127.0.0.1', '10.0.2.2', ]
# tricks to have debug toolbar when developing with docker
if os.environ.get('USE_DOCKER') == 'yes':
    ip = socket.gethostbyname(socket.gethostname())
    INTERNAL_IPS += [ip[:-1] + "1"]

DEBUG_TOOLBAR_CONFIG = {
    'DISABLE_PANELS': [
        'debug_toolbar.panels.redirects.RedirectsPanel',
    ],
    'SHOW_TEMPLATE_CONTEXT': True,
}

# django-extensions
# ------------------------------------------------------------------------------
INSTALLED_APPS += ('django_extensions', )

# TESTING
# ------------------------------------------------------------------------------
TEST_RUNNER = 'django.test.runner.DiscoverRunner'

# Add the HireFire middleware for monitoring queue to scale dynos
# See: https://hirefire.readthedocs.io/
HIREFIRE_PROCS = ['config.procs.WorkerProc']
HIREFIRE_TOKEN = env('HIREFIRE_TOKEN', default="localtest")

# Site URL
SITE_URL = env('SITE_URL', default="http://localhost:8000")

# Github credentials
GITHUB_USERNAME = env('GITHUB_USERNAME')
GITHUB_PASSWORD = env('GITHUB_PASSWORD')
GITHUB_WEBHOOK_BASE_URL = env('GITHUB_WEBHOOK_BASE_URL')
GITHUB_WEBHOOK_SECRET = env('GITHUB_WEBHOOK_SECRET')

# Salesforce OAuth Connected App credentials
CONNECTED_APP_CLIENT_ID = env('CONNECTED_APP_CLIENT_ID')
CONNECTED_APP_CLIENT_SECRET = env('CONNECTED_APP_CLIENT_SECRET')
CONNECTED_APP_CALLBACK_URL = env('CONNECTED_APP_CALLBACK_URL')

GITHUB_STATUS_UPDATES_ENABLED = env.bool('GITHUB_CALLOUTS_ENABLED', False)