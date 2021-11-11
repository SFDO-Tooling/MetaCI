from datetime import timedelta

import pytest
from django.urls import reverse
from django.utils import timezone
from guardian.shortcuts import assign_perm

from metaci.release.models import ReleaseCohort


@pytest.fixture
def cohort():
    return ReleaseCohort.objects.create(
        name="Test Cohort",
        merge_freeze_start=timezone.now(),
        merge_freeze_end=timezone.now(),
    )


@pytest.mark.django_db
class TestReleaseCohortViews:
    def test_cohort_list(self, client, user):
        """Users need to be both logged in *and* have the 'view release cohorts' permission."""
        assign_perm("release.view_releasecohort", user)
        client.force_login(user)
        url = reverse("cohort_list")
        response = client.get(url)

        assert response.status_code == 200

    def test_cohort_list__not_logged_in(self, client):
        url = reverse("cohort_list")
        response = client.get(url)

        assert response.status_code == 403

    def test_cohort_list__logged_in_but_no_perms(self, client, user):
        client.force_login(user)
        url = reverse("cohort_list")
        response = client.get(url)

        assert response.status_code == 403

    def test_cohort_detail__merge_freeze_inactive(self, client, user, cohort):
        """Users need to be both logged in *and* have the 'view release cohorts' permission."""
        assign_perm("release.view_releasecohort", user)
        client.force_login(user)
        url = reverse("cohort_detail", kwargs={"cohort_id": cohort.id})
        response = client.get(url)
        assert response.status_code == 200
        assert not response.context["merge_freeze_active"]

    def test_cohort_detail__merge_freeze_active(self, client, user, cohort):
        """Users need to be both logged in *and* have the 'view release cohorts' permission."""
        cohort.merge_freeze_end = timezone.now() + timedelta(days=1)
        cohort.save()
        assign_perm("release.view_releasecohort", user)
        client.force_login(user)
        url = reverse("cohort_detail", kwargs={"cohort_id": cohort.id})
        response = client.get(url)
        assert response.status_code == 200
        assert response.context["merge_freeze_active"]

    def test_cohort_detail__not_logged_in(self, client, cohort):
        url = reverse("cohort_detail", kwargs={"cohort_id": cohort.id})
        response = client.get(url)

        assert response.status_code == 403

    def test_cohort_detail__logged_in_but_no_perms(self, client, user, cohort):
        client.force_login(user)
        url = reverse("cohort_detail", kwargs={"cohort_id": cohort.id})
        response = client.get(url)

        assert response.status_code == 403
