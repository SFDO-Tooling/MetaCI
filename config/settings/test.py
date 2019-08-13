# -*- coding: utf-8 -*-
"""
Test settings

- Used to run tests fast on the continuous integration server and locally
"""

from .common import *  # noqa

# DEBUG
# ------------------------------------------------------------------------------
# Turn debug off so tests run faster
DEBUG = False
TEMPLATES[0]["OPTIONS"]["debug"] = False

# Allow requests with Host: testserver
ALLOWED_HOSTS = ["testserver"]

# SECRET CONFIGURATION
# ------------------------------------------------------------------------------
# See: https://docs.djangoproject.com/en/dev/ref/settings/#secret-key
# Note: This key only used for development and testing.
SECRET_KEY = env("DJANGO_SECRET_KEY", default="CHANGEME!!!")

# Mail settings
# ------------------------------------------------------------------------------
EMAIL_HOST = "localhost"
EMAIL_PORT = 1025

# In-memory email backend stores messages in django.core.mail.outbox
# for unit testing purposes
EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"

# CACHING
# ------------------------------------------------------------------------------
# Speed advantages of in-memory caching without having to run Memcached
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "",
    }
}

# Use Redis for RQ queues instead of cache which uses LocMemCache
RQ_QUEUES = {
    "default": {"URL": REDIS_URL, "DEFAULT_TIMEOUT": 7200, "AUTOCOMMIT": False},
    "short": {"URL": REDIS_URL, "DEFAULT_TIMEOUT": 500, "AUTOCOMMIT": False},
}


# PASSWORD HASHING
# ------------------------------------------------------------------------------
# Use fast password hasher so tests run faster
PASSWORD_HASHERS = ("django.contrib.auth.hashers.MD5PasswordHasher",)

# TEMPLATE LOADERS
# ------------------------------------------------------------------------------
# Keep templates in memory so tests run faster
TEMPLATES[0]["OPTIONS"]["loaders"] = [
    (
        "django.template.loaders.cached.Loader",
        [
            "django.template.loaders.filesystem.Loader",
            "django.template.loaders.app_directories.Loader",
        ],
    )
]

GITHUB_USERNAME = "TestUser"
GITHUB_PASSWORD = "TestUserPass123"
GITHUB_WEBHOOK_SECRETS = ["a secret"]

# Salesforce OAuth Connected App credentials
CONNECTED_APP_CLIENT_ID = "1234567890"
CONNECTED_APP_CLIENT_SECRET = "abcdefg1234567890"
CONNECTED_APP_CALLBACK_URL = "http://localhost/callback"
