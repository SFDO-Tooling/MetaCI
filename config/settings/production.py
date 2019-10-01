# -*- coding: utf-8 -*-
"""
Production Configurations

- Use Amazon's S3 for storing static files and uploaded media
- Use Sengrid to send emails
- Use Redis for cache

- Use sentry for error logging


"""
from __future__ import absolute_import, unicode_literals

from .common import *  # noqa

# from django.utils import six


# SECRET CONFIGURATION
# ------------------------------------------------------------------------------
# See: https://docs.djangoproject.com/en/dev/ref/settings/#secret-key
# Raises ImproperlyConfigured exception if DJANGO_SECRET_KEY not in os.environ
SECRET_KEY = env("DJANGO_SECRET_KEY")


# This ensures that Django will be able to detect a secure connection
# properly on Heroku.
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
# raven sentry client
# See https://docs.getsentry.com/hosted/clients/python/integrations/django/
INSTALLED_APPS += ("raven.contrib.django.raven_compat",)
INSTALLED_APPS += ("defender",)

# Use Whitenoise to serve static files
# See: https://whitenoise.readthedocs.io/
WHITENOISE_MIDDLEWARE = ("whitenoise.middleware.WhiteNoiseMiddleware",)
MIDDLEWARE = WHITENOISE_MIDDLEWARE + MIDDLEWARE
RAVEN_MIDDLEWARE = (
    "raven.contrib.django.raven_compat.middleware.SentryResponseErrorIdMiddleware",
)
MIDDLEWARE = RAVEN_MIDDLEWARE + MIDDLEWARE
DEFENDER_MIDDLEWARE = ("defender.middleware.FailedLoginMiddleware",)
MIDDLEWARE = MIDDLEWARE + DEFENDER_MIDDLEWARE


# SECURITY CONFIGURATION
# ------------------------------------------------------------------------------
# See https://docs.djangoproject.com/en/1.9/ref/middleware/#module-django.middleware.security
# and https://docs.djangoproject.com/ja/1.9/howto/deployment/checklist/#run-manage-py-check-deploy

# set this to 60 seconds and then to 518400 when you can prove it works
SECURE_HSTS_SECONDS = 60
SECURE_HSTS_INCLUDE_SUBDOMAINS = env.bool(
    "DJANGO_SECURE_HSTS_INCLUDE_SUBDOMAINS", default=True
)
SECURE_CONTENT_TYPE_NOSNIFF = env.bool(
    "DJANGO_SECURE_CONTENT_TYPE_NOSNIFF", default=True
)
SECURE_BROWSER_XSS_FILTER = True
SESSION_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
SECURE_SSL_REDIRECT = env.bool("DJANGO_SECURE_SSL_REDIRECT", default=True)
CSRF_COOKIE_SECURE = True
CSRF_COOKIE_HTTPONLY = True
X_FRAME_OPTIONS = "DENY"

# SITE CONFIGURATION
# ------------------------------------------------------------------------------
# Hosts/domain names that are valid for this site
# See https://docs.djangoproject.com/en/1.6/ref/settings/#allowed-hosts
ALLOWED_HOSTS = env.list("DJANGO_ALLOWED_HOSTS", default=["metaci.herokuapp.com"])
# END SITE CONFIGURATION

INSTALLED_APPS += ("gunicorn",)


# STORAGE CONFIGURATION
# ------------------------------------------------------------------------------
# Uploaded Media Files
# ------------------------
# See: http://django-storages.readthedocs.io/en/latest/index.html
INSTALLED_APPS += ("storages",)

AWS_ACCESS_KEY_ID = env("DJANGO_AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = env("DJANGO_AWS_SECRET_ACCESS_KEY")
AWS_STORAGE_BUCKET_NAME = env("DJANGO_AWS_STORAGE_BUCKET_NAME")
AWS_AUTO_CREATE_BUCKET = True
AWS_BUCKET_ACL = "private"
AWS_DEFAULT_ACL = None

# AWS_S3_CALLING_FORMAT = OrdinaryCallingFormat()

# AWS cache settings, don't change unless you know what you're doing:
# AWS_EXPIRY = 60 * 60 * 24 * 7

# TODO See: https://github.com/jschneier/django-storages/issues/47
# Revert the following and use str after the above-mentioned bug is fixed in
# either django-storage-redux or boto
# AWS_HEADERS = {
#    'Cache-Control': six.b('max-age=%d, s-maxage=%d, must-revalidate' % (
#        AWS_EXPIRY, AWS_EXPIRY))
# }

# URL that handles the media served from MEDIA_ROOT, used for managing
# stored files.
MEDIA_URL = "https://s3.amazonaws.com/{}/".format(AWS_STORAGE_BUCKET_NAME)
DEFAULT_FILE_STORAGE = "config.settings.storage_backends.MediaStorage"

# Static Assets
# ------------------------
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"


# EMAIL
# ------------------------------------------------------------------------------
DEFAULT_FROM_EMAIL = env(
    "DJANGO_DEFAULT_FROM_EMAIL", default="metaci <noreply@metaci.herokuapp.com>"
)
EMAIL_SUBJECT_PREFIX = env("DJANGO_EMAIL_SUBJECT_PREFIX", default="[metaci] ")
SERVER_EMAIL = env("DJANGO_SERVER_EMAIL", default=DEFAULT_FROM_EMAIL)

# Anymail with Sendgrid
INSTALLED_APPS += ("anymail",)
SENDGRID_API_KEY = env("SENDGRID_API_KEY", default=None)
ANYMAIL = {}
ANYMAIL["SENDGRID_API_KEY"] = SENDGRID_API_KEY

EMAIL_BACKEND = "anymail.backends.sendgrid.EmailBackend"

# TEMPLATE CONFIGURATION
# ------------------------------------------------------------------------------
# See:
# https://docs.djangoproject.com/en/dev/ref/templates/api/#django.template.loaders.cached.Loader
TEMPLATES[0]["OPTIONS"]["loaders"] = [
    (
        "django.template.loaders.cached.Loader",
        [
            "django.template.loaders.filesystem.Loader",
            "django.template.loaders.app_directories.Loader",
        ],
    )
]

STATICFILES_DIRS = (
    str(APPS_DIR.path("static")),
    str(ROOT_DIR.path("dist", "prod")),
    str(ROOT_DIR.path("locales")),
    str(ROOT_DIR.path("node_modules/@salesforce-ux")),
)

TEMPLATES[0]["DIRS"] = [
    str(ROOT_DIR.path("dist", "prod")),
    str(APPS_DIR.path("templates")),
]

# DATABASE CONFIGURATION
# ------------------------------------------------------------------------------

# Use the Heroku-style specification
# Raises ImproperlyConfigured exception if DATABASE_URL not in os.environ
DATABASES["default"] = env.db("DATABASE_URL")

# CACHING
# ------------------------------------------------------------------------------

REDIS_MAX_CONNECTIONS = env.int("REDIS_MAX_CONNECTIONS", default=1)
REDIS_LOCATION = "{0}/{1}".format(env("REDIS_URL", default="redis://127.0.0.1:6379"), 0)
# Heroku URL does not pass the DB number, so we parse it in
CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": REDIS_LOCATION,
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


# Logging configuration, heroku logfmt
# 12FA logs to stdout only.
# request_id injected into logstream for all lines
LOGGING = {
    "version": 1,
    "disable_existing_loggers": True,
    "root": {"level": "WARNING", "handlers": []},
    "filters": {"request_id": {"()": "log_request_id.filters.RequestIDFilter"}},
    "formatters": {
        "logfmt": {
            "format": "at=%(levelname)-8s request_id=%(request_id)s module=%(name)s %(message)s"
        },
        "simple": {"format": "at=%(levelname)-8s module=%(name)s msg=%(message)s"},
    },
    "handlers": {
        "console_w_req": {
            "level": "DEBUG",
            "class": "logging.StreamHandler",
            "filters": ["request_id"],
            "formatter": "logfmt",
        },
        "console": {
            "level": "DEBUG",
            "class": "logging.StreamHandler",
            "filters": ["request_id"],
            "formatter": "simple",
        },
    },
    "loggers": {
        "django": {"level": "ERROR", "handlers": ["console_w_req"], "propagate": False},
        "raven": {"level": "DEBUG", "handlers": ["console_w_req"], "propagate": False},
        "log_request_id.middleware": {
            "handlers": ["console_w_req"],
            "level": "DEBUG",
            "propagate": False,
        },
        "rq.worker": {"handlers": ["console"], "level": "DEBUG", "propagate": False},
        "metaci": {"handlers": ["console"], "level": "INFO", "propagate": False},
    },
}

# Sentry Configuration
SENTRY_DSN = env("DJANGO_SENTRY_DSN", default=None)
SENTRY_CLIENT = env(
    "DJANGO_SENTRY_CLIENT", default="raven.contrib.django.raven_compat.DjangoClient"
)

RAVEN_CONFIG = {}
if SENTRY_DSN:
    RAVEN_CONFIG["DSN"] = SENTRY_DSN
    LOGGING["handlers"]["sentry"] = {
        "level": "ERROR",
        "class": "raven.contrib.django.raven_compat.handlers.SentryHandler",
    }
    LOGGING["loggers"]["sentry.errors"] = {
        "level": "DEBUG",
        "handlers": ["console"],
        "propagate": False,
    }
    LOGGING["root"]["handlers"].append("sentry")
    LOGGING["loggers"]["django"]["handlers"].append("sentry")

# Add the HireFire middleware for monitoring queue to scale dynos
# See: https://hirefire.readthedocs.io/
HIREFIRE_TOKEN = env("HIREFIRE_TOKEN", default=None)
if HIREFIRE_TOKEN:
    HIREFIRE_PROCS = ["config.procs.WorkerProc"]

HEROKU_TOKEN = env("HEROKU_TOKEN", default=None)
HEROKU_APP_NAME = env("HEROKU_APP_NAME", default=None)
if HEROKU_TOKEN and HEROKU_APP_NAME:
    METACI_WORKER_AUTOSCALER = "metaci.build.autoscaling.HerokuAutoscaler"

# Custom Admin URL, use {% url 'admin:index' %}
ADMIN_URL = env("DJANGO_ADMIN_URL")

# Site URL: assumes appname.herokuapp.com
SITE_URL = env("SITE_URL")
FROM_EMAIL = env("FROM_EMAIL")

# Github credentials
GITHUB_WEBHOOK_SECRET = env("GITHUB_WEBHOOK_SECRET")

# Salesforce OAuth Connected App credentials
CONNECTED_APP_CLIENT_ID = env("CONNECTED_APP_CLIENT_ID")
CONNECTED_APP_CLIENT_SECRET = env("CONNECTED_APP_CLIENT_SECRET")
CONNECTED_APP_CALLBACK_URL = env("CONNECTED_APP_CALLBACK_URL")

SFDX_CLIENT_ID = env("SFDX_CLIENT_ID")
SFDX_HUB_KEY = env("SFDX_HUB_KEY")
SFDX_HUB_USERNAME = env("SFDX_HUB_USERNAME")

# django-defender configuration
DEFENDER_REDIS_NAME = "default"
