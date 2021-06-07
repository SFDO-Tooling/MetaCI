import os


def get_release_values(request):
    return {
        "METACI_RELEASE_WEBHOOK_URL": os.environ.get(
            "METACI_RELEASE_WEBHOOK_URL", None
        ),
    }
