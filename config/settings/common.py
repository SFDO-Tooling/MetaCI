# -*- coding: utf-8 -*-
"""
Django settings for metaci project.

For more information on this file, see
https://docs.djangoproject.com/en/dev/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/dev/ref/settings/
"""
from __future__ import absolute_import, unicode_literals

from ipaddress import IPv4Network
from typing import List

import environ

ROOT_DIR = (
    environ.Path(__file__) - 3
)  # (metaci/config/settings/common.py - 3 = metaci/)
APPS_DIR = ROOT_DIR.path("metaci")

env = environ.Env()
env.read_env()


def ipv4_networks(val: str) -> List[IPv4Network]:
    return [IPv4Network(s.strip()) for s in val.split(",")]


def url_prefix(val: str) -> str:
    return val.rstrip("/") + "/"


def url_prefix_list(val: str) -> List[str]:
    return [url_prefix(url) for url in val.split(",")]


# APP CONFIGURATION
# ------------------------------------------------------------------------------
DJANGO_APPS = (
    # Default Django apps:
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.sites",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Useful template tags:
    "django.contrib.humanize",
    # Admin
    "django.contrib.admin",
)
THIRD_PARTY_APPS = (
    "allauth",  # registration
    "allauth.account",  # registration
    "allauth.socialaccount",  # registration
    "allauth.socialaccount.providers.github",  # github
    "crispy_forms",  # Form layouts
    "django_filters",  # view helpers for filtering models
    "django_js_reverse",  # allow JS to reverse URLs
    "django_rq",
    "django_slds_crispyforms",  # SLDS theme for crispyforms
    "guardian",  # Per Object Permissions via django-guardian
    "rest_framework",  # API
    "rest_framework.authtoken",
    "scheduler",  # django-rq-scheduler
    "watson",  # Full text search
)

# Apps specific for this project go here.
LOCAL_APPS = (
    "metaci.users.apps.UsersConfig",
    "metaci.api.apps.ApiConfig",
    "metaci.build.apps.BuildConfig",
    "metaci.create_org.apps.CreateOrgConfig",
    "metaci.cumulusci.apps.CumulusCIConfig",
    "metaci.notification.apps.NotificationConfig",
    "metaci.plan.apps.PlanConfig",
    "metaci.repository.apps.RepositoryConfig",
    "metaci.testresults.apps.TestResultsConfig",
    "metaci.release.apps.ReleaseConfig",
    "metaci.db.apps.DBUtils",
)

# See: https://docs.djangoproject.com/en/dev/ref/settings/#installed-apps
INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

ALLOWED_HOSTS = [
    "127.0.0.1",
    "127.0.0.1:8000",
    "127.0.0.1:8080",
    "localhost",
    "localhost:8000",
    "localhost:8080",
]

# MIDDLEWARE CONFIGURATION
# ------------------------------------------------------------------------------
MIDDLEWARE = (
    "log_request_id.middleware.RequestIDMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "sfdo_template_helpers.admin.middleware.AdminRestrictMiddleware",
)

# MIGRATIONS CONFIGURATION
# ------------------------------------------------------------------------------
MIGRATION_MODULES = {"sites": "metaci.contrib.sites.migrations"}

# DEBUG
# ------------------------------------------------------------------------------
# See: https://docs.djangoproject.com/en/dev/ref/settings/#debug
DEBUG = env.bool("DJANGO_DEBUG", False)

# FIXTURE CONFIGURATION
# ------------------------------------------------------------------------------
# See: https://docs.djangoproject.com/en/dev/ref/settings/#std:setting-FIXTURE_DIRS
FIXTURE_DIRS = (str(APPS_DIR.path("fixtures")),)

# EMAIL CONFIGURATION
# ------------------------------------------------------------------------------
EMAIL_BACKEND = env(
    "DJANGO_EMAIL_BACKEND", default="django.core.mail.backends.smtp.EmailBackend"
)

# MANAGER CONFIGURATION
# ------------------------------------------------------------------------------
# See: https://docs.djangoproject.com/en/dev/ref/settings/#admins
ADMINS = ()

# See: https://docs.djangoproject.com/en/dev/ref/settings/#managers
MANAGERS = ADMINS

# DATABASE CONFIGURATION
# ------------------------------------------------------------------------------
# See: https://docs.djangoproject.com/en/dev/ref/settings/#databases
DATABASES = {"default": env.db("DATABASE_URL", default="sqlite:///ci.db")}
DATABASES["default"]["ATOMIC_REQUESTS"] = True


# GENERAL CONFIGURATION
# ------------------------------------------------------------------------------
# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# In a Windows environment this must be set to your system time zone.
TIME_ZONE = env("DJANGO_TIME_ZONE", default="UTC")

# See: https://docs.djangoproject.com/en/dev/ref/settings/#language-code
LANGUAGE_CODE = "en-us"

# See: https://docs.djangoproject.com/en/dev/ref/settings/#site-id
SITE_ID = 1

# See: https://docs.djangoproject.com/en/dev/ref/settings/#use-i18n
USE_I18N = True

# See: https://docs.djangoproject.com/en/dev/ref/settings/#use-l10n
USE_L10N = True

# See: https://docs.djangoproject.com/en/dev/ref/settings/#use-tz
USE_TZ = True

# TEMPLATE CONFIGURATION
# ------------------------------------------------------------------------------
# See: https://docs.djangoproject.com/en/dev/ref/settings/#templates
TEMPLATES = [
    {
        # See: https://docs.djangoproject.com/en/dev/ref/settings/#std:setting-TEMPLATES-BACKEND
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        # See: https://docs.djangoproject.com/en/dev/ref/settings/#template-dirs
        # This gets overridden in settings.production:
        "DIRS": [str(ROOT_DIR.path("dist")), str(APPS_DIR.path("templates"))],
        "OPTIONS": {
            # See: https://docs.djangoproject.com/en/dev/ref/settings/#template-debug
            "debug": DEBUG,
            # See: https://docs.djangoproject.com/en/dev/ref/settings/#template-loaders
            # https://docs.djangoproject.com/en/dev/ref/templates/api/#loader-types
            "loaders": [
                "django.template.loaders.filesystem.Loader",
                "django.template.loaders.app_directories.Loader",
            ],
            # See: https://docs.djangoproject.com/en/dev/ref/settings/#template-context-processors
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.template.context_processors.i18n",
                "django.template.context_processors.media",
                "django.template.context_processors.static",
                "django.template.context_processors.tz",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    }
]

# See: http://django-crispy-forms.readthedocs.io/en/latest/install.html#template-packs
CRISPY_TEMPLATE_PACK = "bootstrap4"

# STATIC FILE CONFIGURATION
# ------------------------------------------------------------------------------
# See: https://docs.djangoproject.com/en/dev/ref/settings/#static-root
STATIC_ROOT = str(ROOT_DIR("staticfiles"))

# See: https://docs.djangoproject.com/en/dev/ref/settings/#static-url
STATIC_URL = "/static/"

# See: https://docs.djangoproject.com/en/dev/ref/contrib/staticfiles/#std:setting-STATICFILES_DIRS
STATICFILES_DIRS = (
    str(APPS_DIR.path("static")),
    str(ROOT_DIR.path("dist")),
    str(ROOT_DIR.path("locales")),
    str(ROOT_DIR.path("node_modules/@salesforce-ux")),
)

# See: https://docs.djangoproject.com/en/dev/ref/contrib/staticfiles/#staticfiles-finders
STATICFILES_FINDERS = (
    "django.contrib.staticfiles.finders.FileSystemFinder",
    "django.contrib.staticfiles.finders.AppDirectoriesFinder",
)

# MEDIA CONFIGURATION
# ------------------------------------------------------------------------------
# See: https://docs.djangoproject.com/en/dev/ref/settings/#media-root
MEDIA_ROOT = str(APPS_DIR("media"))

# See: https://docs.djangoproject.com/en/dev/ref/settings/#media-url
MEDIA_URL = "/media/"

# URL Configuration
# ------------------------------------------------------------------------------
ROOT_URLCONF = "config.urls"

# Location of root django.contrib.admin URL, use {% url 'admin:index' %}
ADMIN_URL = env("DJANGO_ADMIN_URL", default="admin")
ADMIN_URL_ROUTE = r"^{}/".format(ADMIN_URL)

# Forward-compatible alias for use with IP-checking middleware
ADMIN_AREA_PREFIX = ADMIN_URL

# URLs other than ADMIN_AREA which should be secure
RESTRICTED_PREFIXES = env("RESTRICTED_PREFIXES", default=[], cast=url_prefix_list)

ADMIN_API_ALLOWED_SUBNETS = env(
    "ADMIN_API_ALLOWED_SUBNETS",
    default="0.0.0.0/0",
    cast=ipv4_networks,
    parse_default=True,
)

# See: https://docs.djangoproject.com/en/dev/ref/settings/#wsgi-application
WSGI_APPLICATION = "config.wsgi.application"


# PASSWORD VALIDATION
# https://docs.djangoproject.com/en/dev/ref/settings/#auth-password-validators
# ------------------------------------------------------------------------------

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"
    },
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# AUTHENTICATION CONFIGURATION
# ------------------------------------------------------------------------------
AUTHENTICATION_BACKENDS = (
    "django.contrib.auth.backends.ModelBackend",
    "allauth.account.auth_backends.AuthenticationBackend",
    "guardian.backends.ObjectPermissionBackend",
)

# Some really nice defaults
ACCOUNT_AUTHENTICATION_METHOD = "username"
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_EMAIL_VERIFICATION = "mandatory"

ACCOUNT_ALLOW_REGISTRATION = env.bool("DJANGO_ACCOUNT_ALLOW_REGISTRATION", True)
ACCOUNT_ADAPTER = "metaci.users.adapters.AccountAdapter"
SOCIALACCOUNT_ADAPTER = "metaci.users.adapters.SocialAccountAdapter"

# Custom user app defaults
# Select the correct user model
AUTH_USER_MODEL = "users.User"
LOGIN_REDIRECT_URL = "users:redirect"
LOGIN_URL = "account_login"

# SLUGLIFIER
AUTOSLUG_SLUGIFY_FUNCTION = "slugify.slugify"

# django-rq
REDIS_URL = env("REDIS_URL", default="redis://localhost:6379")
REDIS_URL += "/0"
RQ_QUEUES = {
    "default": {
        "USE_REDIS_CACHE": "default",
        "DEFAULT_TIMEOUT": 7200,
        "AUTOCOMMIT": False,
    },
    "short": {
        "USE_REDIS_CACHE": "default",
        "DEFAULT_TIMEOUT": 500,
        "AUTOCOMMIT": False,
    },
}

# Site URL
SITE_URL = None
FROM_EMAIL = "test@mailinator.com"

# Github credentials
GITHUB_USERNAME = env("GITHUB_USERNAME", default=None)
GITHUB_PASSWORD = env("GITHUB_PASSWORD", default=None)
GITHUB_WEBHOOK_SECRET = None

# Salesforce OAuth Connected App credentials
CONNECTED_APP_CLIENT_ID = None
CONNECTED_APP_CLIENT_SECRET = None
CONNECTED_APP_CALLBACK_URL = None
SFDX_CLIENT_ID = None
SFDX_HUB_KEY = None
SFDX_HUB_USERNAME = None

# Application Behaviors
GITHUB_STATUS_UPDATES_ENABLED = env.bool("GITHUB_STATUS_UPDATES_ENABLED", True)
METACI_FLOW_CALLBACK_ENABLED = env.bool("METACI_FLOW_CALLBACK_ENABLED", True)

# Number of scratch orgs to leave available in the org.
SCRATCH_ORG_RESERVE = env.int("METACI_SCRATCH_ORG_RESERVE", 10)

# Autoscaler class used for scaling the worker formation
METACI_WORKER_AUTOSCALER = env("METACI_WORKER_AUTOSCALER", default=None)
# What's the max number of worker dynos we should scale up to
METACI_MAX_WORKERS = env.int("METACI_MAX_WORKERS", 3)
# How many worker slots to reserve for high-priority jobs.
# Should be less than METACI_MAX_WORKERS
METACI_WORKER_RESERVE = env.int("METACI_WORKER_RESERVE", 1)

# Django REST Framework
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework.authentication.BasicAuthentication",
        "rest_framework.authentication.TokenAuthentication",
        "rest_framework.authentication.SessionAuthentication",
    ),
    "DEFAULT_FILTER_BACKENDS": ("django_filters.rest_framework.DjangoFilterBackend",),
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 100,
    "DEFAULT_PERMISSION_CLASSES": (
        "metaci.api.permissions.IsOnSecureNetwork",
        "rest_framework.permissions.IsAdminUser",
    ),
}

# log_request_id settings
LOG_REQUEST_ID_HEADER = "HTTP_X_REQUEST_ID"
LOG_REQUESTS = True
GENERATE_REQUEST_ID_IF_NOT_IN_HEADER = True
REQUEST_ID_RESPONSE_HEADER = "X-Request-ID"

# django-guardian settings
GUARDIAN_MONKEY_PATCH = False

JS_REVERSE_JS_VAR_NAME = "api_urls"
JS_REVERSE_EXCLUDE_NAMESPACES = ["admin", "admin_rest"]
