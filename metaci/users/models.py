from django.contrib.auth.models import AbstractUser
from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from guardian.mixins import GuardianUserMixin


class User(GuardianUserMixin, AbstractUser):

    # First Name and Last Name do not cover name patterns
    # around the globe.
    name = models.CharField(_("Name of User"), blank=True, max_length=255)

    def __str__(self):
        return self.username

    def get_absolute_url(self):
        return reverse("users:detail", kwargs={"username": self.username})

    def has_perm(self, perm, obj=None):
        if obj is not None:
            has_local_perm = super(User, self).has_perm(perm, obj)
        else:
            has_local_perm = False
        has_global_perm = super(User, self).has_perm(perm)
        return has_local_perm or has_global_perm
