from cumulusci.core.config import ConnectedAppOAuthConfig
from django.conf import settings


def get_connected_app():
    return ConnectedAppOAuthConfig(
        {
            "callback_url": settings.CONNECTED_APP_CALLBACK_URL,
            "client_id": settings.CONNECTED_APP_CLIENT_ID,
            "client_secret": settings.CONNECTED_APP_CLIENT_SECRET,
        }
    )
