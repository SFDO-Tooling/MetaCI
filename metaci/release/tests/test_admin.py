import pytest
from django.contrib.admin.sites import AdminSite
from django.test import RequestFactory

from metaci.fixtures.factories import ReleaseFactory

from ..admin import ReleaseAdmin
from ..models import Release


@pytest.mark.django_db
def test_release_admin_init_from_repo():
    release = ReleaseFactory(version_number="1.0")
    repo = release.repo

    admin = ReleaseAdmin(model=Release, admin_site=AdminSite())
    request = RequestFactory().get(f"/?repo_id={repo.pk}")
    form = admin.get_form(request)

    assert form.base_fields["repo"].initial == repo
    assert form.base_fields["version_number"].initial == "1.1"
