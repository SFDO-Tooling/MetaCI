"""
Test settings

- Used to run tests fast on the continuous integration server and locally
"""

from cryptography.fernet import Fernet

from .base import *  # noqa

INSTALLED_APPS += ("metaci.tests",)

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

DB_ENCRYPTION_KEYS = [Fernet.generate_key()]

# Mail settings
# ------------------------------------------------------------------------------
EMAIL_HOST = "localhost"
EMAIL_PORT = 1025

# In-memory email backend stores messages in django.core.mail.outbox
# for unit testing purposes
EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"


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

HEROKU_TOKEN = "BOGUS"
HEROKU_APP_NAME = "testapp"

METACI_WORKER_AUTOSCALER = "metaci.build.autoscaling.LocalAutoscaler"

AUTOSCALERS = {
    "test-app": {
        "app_name": "test-app",
        "worker_type": "worker",
        "max_workers": 2,
        "worker_reserve": 1,
        "queues": ["default", "medium", "high"],
    }
}

METACI_LONG_RUNNING_BUILD_CONFIG = {"app_name": "test-app"}
METACI_LONG_RUNNING_BUILD_CLASS = "metaci.build.autoscaling.LocalOneOffBuilder"

METACI_RELEASE_WEBHOOK_AUTH_KEY = "12345"
METACI_RELEASE_WEBHOOK_ISSUER = "MetaCI"
METACI_RELEASE_WEBHOOK_URL = "https://webhook"

SITE_URL = "https://webhook"
