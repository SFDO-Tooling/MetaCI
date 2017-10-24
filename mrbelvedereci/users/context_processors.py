from django.conf import settings

def admin_url(request):
    return {'ADMIN_URL': settings.ADMIN_URL}
