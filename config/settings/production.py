# flake8: noqa: F405
"""
Production Configurations

- Use Amazon's S3 for storing static files and uploaded media
- Use Mailgun to send emails
- Use Redis for cache

"""
import json
import ssl

from .base import *  # noqa

# SECRET CONFIGURATION
# ------------------------------------------------------------------------------
# See: https://docs.djangoproject.com/en/dev/ref/settings/#secret-key
# Raises ImproperlyConfigured exception if DJANGO_SECRET_KEY not in os.environ
SECRET_KEY = env("DJANGO_SECRET_KEY")

DB_ENCRYPTION_KEYS = env("DB_ENCRYPTION_KEYS", cast=nl_separated_bytes_list)

# This ensures that Django will be able to detect a secure connection
# properly on Heroku.
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

INSTALLED_APPS += ("defender",)

# Use Whitenoise to serve static files
# See: https://whitenoise.readthedocs.io/
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
LANGUAGE_COOKIE_HTTPONLY = True

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
AWS_S3_OBJECT_PARAMETERS = {}
s3_sse = env("DJANGO_AWS_S3_ENCRYPTION", default=None)
if s3_sse is not None:
    AWS_S3_OBJECT_PARAMETERS["ServerSideEncryption"] = s3_sse


# URL that handles the media served from MEDIA_ROOT, used for managing
# stored files.
MEDIA_URL = f"https://s3.amazonaws.com/{AWS_STORAGE_BUCKET_NAME}/"
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

# Anymail with Mailgun
INSTALLED_APPS += ("anymail",)
MAILGUN_API_KEY = env("MAILGUN_API_KEY", default=None)
ANYMAIL = {}
ANYMAIL["MAILGUN_API_KEY"] = MAILGUN_API_KEY
ANYMAIL["MAILGUN_SENDER_DOMAIN"] = env("MAILGUN_DOMAIN", default=None)

EMAIL_BACKEND = "anymail.backends.mailgun.EmailBackend"

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
        "log_request_id.middleware": {
            "handlers": ["console_w_req"],
            "level": "DEBUG",
            "propagate": False,
        },
        "rq.worker": {"handlers": ["console"], "level": "DEBUG", "propagate": False},
        "metaci": {"handlers": ["console"], "level": "INFO", "propagate": False},
    },
}

# Add the HireFire middleware for monitoring queue to scale dynos
# See: https://hirefire.readthedocs.io/
HIREFIRE_TOKEN = env("HIREFIRE_TOKEN", default=None)
if HIREFIRE_TOKEN:
    HIREFIRE_PROCS = ["config.procs.WorkerProc"]

HEROKU_TOKEN = env("HEROKU_TOKEN", default=None)
HEROKU_APP_NAME = env("HEROKU_APP_NAME", default=None)

if HEROKU_TOKEN and HEROKU_APP_NAME:
    METACI_WORKER_AUTOSCALER = "metaci.build.autoscaling.HerokuAutoscaler"
    METACI_LONG_RUNNING_BUILD_CLASS = "metaci.build.autoscaling.HerokuOneOffBuilder"

# Autoscalers are defined per METACI_APP
AUTOSCALERS = json.loads(env("AUTOSCALERS", default="{}"))

if not AUTOSCALERS and HEROKU_APP_NAME:
    # backwards compatability
    AUTOSCALERS = {
        HEROKU_APP_NAME: {
            "app_name": HEROKU_APP_NAME,
            "worker_type": WORKER_DYNO_NAME,
            "max_workers": METACI_MAX_WORKERS,
            "worker_reserve": METACI_WORKER_RESERVE,
            "queues": ["default", "medium", "high"],
        }
    }

# Custom Admin URL, use {% url 'admin:index' %}
ADMIN_URL = env("DJANGO_ADMIN_URL")

# Site URL: assumes appname.herokuapp.com
SITE_URL = env("SITE_URL")
FROM_EMAIL = env("FROM_EMAIL")

# Salesforce OAuth Connected App credentials
SFDX_CLIENT_ID = env("SFDX_CLIENT_ID")
SFDX_HUB_KEY = env("SFDX_HUB_KEY")
SFDX_HUB_USERNAME = env("SFDX_HUB_USERNAME")

# django-defender configuration
DEFENDER_REDIS_NAME = "default"

if REDIS_LOCATION.startswith("rediss://"):
    # Fix Redis errors with Heroku self-signed certificates
    # See:
    #   - https://github.com/jazzband/django-redis/issues/353
    CACHES["default"]["OPTIONS"]["CONNECTION_POOL_KWARGS"] = {"ssl_cert_reqs": False}
