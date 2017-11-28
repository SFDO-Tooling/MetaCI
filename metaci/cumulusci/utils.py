from datetime import date, datetime
from cumulusci.core.config import ConnectedAppOAuthConfig
from django.conf import settings

def get_connected_app():
    return ConnectedAppOAuthConfig({
        'callback_url': settings.CONNECTED_APP_CALLBACK_URL,
        'client_id': settings.CONNECTED_APP_CLIENT_ID,
        'client_secret': settings.CONNECTED_APP_CLIENT_SECRET,
    })

def json_serial(obj):
    """JSON serializer for objects not serializable by default json code"""

    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    raise TypeError ("Type %s not serializable" % type(obj))

