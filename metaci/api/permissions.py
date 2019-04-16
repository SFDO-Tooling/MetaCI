from django.core.exceptions import PermissionDenied, SuspiciousOperation
from rest_framework.permissions import BasePermission
from sfdo_template_helpers.admin.middleware import AdminRestrictMiddleware


class IsOnSecureNetwork(BasePermission):
    def has_permission(self, request, view):
        try:
            # TODO: Should really rename _validate_ip to remove underscore.
            AdminRestrictMiddleware(None)._validate_ip(request)
        except SuspiciousOperation as e:
            raise PermissionDenied(*e.args)

        return True
