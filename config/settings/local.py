# -*- coding: utf-8 -*-
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

from .common import *

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

# Mail settings
# ------------------------------------------------------------------------------

EMAIL_PORT = 1025

EMAIL_HOST = "localhost"
EMAIL_BACKEND = env(
    "DJANGO_EMAIL_BACKEND", default="django.core.mail.backends.console.EmailBackend"
)


# CACHING
# ------------------------------------------------------------------------------
REDIS_MAX_CONNECTIONS = env.int("REDIS_MAX_CONNECTIONS", default=1)
CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": REDIS_URL,
        "OPTIONS": {
            "CONNECTION_POOL_CLASS": "redis.BlockingConnectionPool",
            "CONNECTION_POOL_KWARGS": {
                "max_connections": REDIS_MAX_CONNECTIONS,
                "timeout": 20,
            },
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
            "IGNORE_EXCEPTIONS": True,  # mimics memcache behavior.
            # http://niwinz.github.io/django-redis/latest/#_memcached_exceptions_behavior
        },
    }
}

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
# MEDIA_URL = 'https://s3.amazonaws.com/{}/'.format(AWS_STORAGE_BUCKET_NAME)
# DEFAULT_FILE_STORAGE = 'config.settings.storage_backends.MediaStorage'

# TESTING
# ------------------------------------------------------------------------------
TEST_RUNNER = "django.test.runner.DiscoverRunner"

# Add the HireFire middleware for monitoring queue to scale dynos
# See: https://hirefire.readthedocs.io/
HIREFIRE_PROCS = ["config.procs.WorkerProc"]
HIREFIRE_TOKEN = env("HIREFIRE_TOKEN", default="localtest")

METACI_WORKER_AUTOSCALER = "metaci.build.autoscaling.LocalAutoscaler"

# Site URL
SITE_URL = env("SITE_URL", default="http://localhost:8000")

# Github credentials
GITHUB_WEBHOOK_SECRET = env("GITHUB_WEBHOOK_SECRET")
GITHUB_STATUS_UPDATES_ENABLED = env.bool("GITHUB_STATUS_UPDATES_ENABLED", False)

# Salesforce OAuth Connected App credentials
CONNECTED_APP_CLIENT_ID = env("CONNECTED_APP_CLIENT_ID")
CONNECTED_APP_CLIENT_SECRET = env("CONNECTED_APP_CLIENT_SECRET")
CONNECTED_APP_CALLBACK_URL = env("CONNECTED_APP_CALLBACK_URL")

# SFDX Credentials
SFDX_CLIENT_ID = env("SFDX_CLIENT_ID")
SFDX_HUB_KEY = env("SFDX_HUB_KEY")
SFDX_HUB_USERNAME = env("SFDX_HUB_USERNAME")

SECURE_SSL_REDIRECT = env.bool("DJANGO_SECURE_SSL_REDIRECT", default=False)

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {"console": {"class": "logging.StreamHandler"}},
    "loggers": {"metaci": {"handlers": ["console"], "level": "DEBUG"}},
}
