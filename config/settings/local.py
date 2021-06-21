# flake8: noqa: F405
"""
Local settings

- Run in Debug mode

- Use console backend for emails

- Add Django Debug Toolbar
- Add django-extensions as app
"""

import os
import socket

from .base import *

# DEBUG
# ------------------------------------------------------------------------------
DEBUG = env.bool("DJANGO_DEBUG", default=True)
TEMPLATES[0]["OPTIONS"]["debug"] = DEBUG

# SECRET CONFIGURATION
# ------------------------------------------------------------------------------
# See: https://docs.djangoproject.com/en/dev/ref/settings/#secret-key
# Note: This key only used for development and testing.
SECRET_KEY = env(
    "DJANGO_SECRET_KEY", default="!)_b4xaov6!0b^_=96*wh@p-9si4p0ho-@4&g7eija9gaxhmo!"
)

DB_ENCRYPTION_KEYS = env("DB_ENCRYPTION_KEYS", cast=nl_separated_bytes_list)

# Mail settings
# ------------------------------------------------------------------------------

EMAIL_PORT = 1025

EMAIL_HOST = "localhost"
EMAIL_BACKEND = env(
    "DJANGO_EMAIL_BACKEND", default="django.core.mail.backends.console.EmailBackend"
)


# django-debug-toolbar
# ------------------------------------------------------------------------------
MIDDLEWARE += ("debug_toolbar.middleware.DebugToolbarMiddleware",)
INSTALLED_APPS += ("debug_toolbar",)

INTERNAL_IPS = ["127.0.0.1", "10.0.2.2"]
# tricks to have debug toolbar when developing with docker
if os.environ.get("USE_DOCKER") == "yes":
    ip = socket.gethostbyname(socket.gethostname())
    INTERNAL_IPS += [ip[:-1] + "1"]

DEBUG_TOOLBAR_CONFIG = {
    "DISABLE_PANELS": ["debug_toolbar.panels.redirects.RedirectsPanel"],
    "SHOW_TEMPLATE_CONTEXT": True,
}

# django-extensions
# ------------------------------------------------------------------------------
INSTALLED_APPS += ("django_extensions",)

# STORAGE CONFIGURATION
# ------------------------------------------------------------------------------
# Uploaded Media Files
# ------------------------
# See: http://django-storages.readthedocs.io/en/latest/index.html
# INSTALLED_APPS += (
#    'storages',
# )

# AWS_ACCESS_KEY_ID = env('DJANGO_AWS_ACCESS_KEY_ID')
# AWS_SECRET_ACCESS_KEY = env('DJANGO_AWS_SECRET_ACCESS_KEY')
# AWS_STORAGE_BUCKET_NAME = env('DJANGO_AWS_STORAGE_BUCKET_NAME')
# AWS_AUTO_CREATE_BUCKET = True
# AWS_QUERYSTRING_AUTH = False

# URL that handles the media served from MEDIA_ROOT, used for managing
# stored files.
# MEDIA_URL = f'https://s3.amazonaws.com/{AWS_STORAGE_BUCKET_NAME}/'
# DEFAULT_FILE_STORAGE = 'config.settings.storage_backends.MediaStorage'

# TESTING
# ------------------------------------------------------------------------------
TEST_RUNNER = "django.test.runner.DiscoverRunner"

# Add the HireFire middleware for monitoring queue to scale dynos
# See: https://hirefire.readthedocs.io/
HIREFIRE_PROCS = ["config.procs.WorkerProc"]
HIREFIRE_TOKEN = env("HIREFIRE_TOKEN", default="localtest")

METACI_WORKER_AUTOSCALER = "metaci.build.autoscaling.LocalAutoscaler"
ALLOWED_HOSTS = [
    "127.0.0.1",
    "127.0.0.1:8000",
    "127.0.0.1:8080",
    "localhost",
    "0.0.0.0:8000",
    "localhost:8000",
    "localhost:8080",
    "0.0.0.0",
]
METACI_LONG_RUNNING_BUILD_CLASS = "metaci.build.autoscaling.LocalOneOffBuilder"
# Site URL
SITE_URL = env("SITE_URL", default="http://localhost:8000")

# Github credentials
GITHUB_STATUS_UPDATES_ENABLED = env.bool("GITHUB_STATUS_UPDATES_ENABLED", False)

AUTOSCALERS = {
    "local-app": {
        "max_workers": METACI_MAX_WORKERS or 1,
        "worker_reserve": METACI_WORKER_RESERVE or 0,
        "queues": ["default", "medium", "high", "robot"],
    }
}

# SFDX Credentials
SFDX_CLIENT_ID = env("SFDX_CLIENT_ID", default=None)
SFDX_HUB_KEY = env("SFDX_HUB_KEY", default="").replace(r"\n", "\n")
SFDX_HUB_USERNAME = env("SFDX_HUB_USERNAME", default=None)

SECURE_SSL_REDIRECT = env.bool("DJANGO_SECURE_SSL_REDIRECT", default=False)

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {"console": {"class": "logging.StreamHandler"}},
    "loggers": {"metaci": {"handlers": ["console"], "level": "DEBUG"}},
}
