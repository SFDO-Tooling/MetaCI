from unittest.mock import Mock

import pytest

from metaci.release.models import ImplementationStep

from ...fixtures.factories import PlanFactory, ReleaseFactory
from ..utils import send_release_webhook, send_submit_webhook


def test_send_release_webhook(mocked_responses, mocker, transactional_db):
    mocker.patch(
        "metaci.release.utils.settings",
        METACI_RELEASE_WEBHOOK_URL="https://webhook",
        METACI_CHANGE_CASE_URL_TEMPLATE="{case_id}",
        METACI_RELEASE_WEBHOOK_ISSUER="MetaCI",
        METACI_RELEASE_WEBHOOK_AUTH_KEY="test",
        GUS_BUS_OWNER_ID="00G",
    )
    mocked_responses.add(
        "POST",
        "https://webhook/release/",
        json={"success": True, "implementationSteps": ["2", "1", "3"], "id": "2"},
    )

    project_config = Mock(project__package__name="Test Package")
    project_config.get_version_for_tag.return_value = "1.0"
    release = ReleaseFactory()
    test_plan = PlanFactory()
    second_plan = PlanFactory(role="foo")
    release.implementation_steps.set(
        [
            ImplementationStep(
                release=release,
                plan=test_plan,
                external_id="",
                start_time="2021-06-08T08:00:00+00:00",
                stop_time="2021-06-09T18:00:00+00:00",
            ),
            ImplementationStep(
                release=release,
                plan=second_plan,
                external_id="",
                start_time="2021-06-08T08:00:00+00:00",
                stop_time="2021-06-09T18:00:00+00:00",
            ),
        ],
        bulk=False,
    )
    send_release_webhook(release, "INFRA.instance1")
    assert release.implementation_steps.get(plan__role="test").external_id == "2"
    assert release.implementation_steps.get(plan__role="foo").external_id == "1"
    assert release.change_case_link == "2"


def test_send_release_webhook__disabled(mocked_responses):
    send_release_webhook(None, None)
    assert len(mocked_responses.calls) == 0


def test_send_release_webhook__error(mocked_responses, mocker, transactional_db):
    mocker.patch(
        "metaci.release.utils.settings",
        METACI_RELEASE_WEBHOOK_URL="https://webhook",
        METACI_RELEASE_WEBHOOK_ISSUER="MetaCI",
        METACI_RELEASE_WEBHOOK_AUTH_KEY="test",
    )
    mocked_responses.add(
        "POST",
        "https://webhook/release/",
        json={
            "success": False,
            "errors": [
                {"message": "ImplementationStep matching query does not exist."}
            ],
        },
    )

    project_config = Mock(project__package__name="Test Package")
    project_config.get_version_for_tag.return_value = "1.0"
    release = ReleaseFactory()

    with pytest.raises(
        Exception, match="ImplementationStep matching query does not exist."
    ):
        send_release_webhook(release, "INFRA.instance1")


def test_send_submit_webhook(mocked_responses, mocker, transactional_db):
    mocker.patch(
        "metaci.release.utils.settings",
        METACI_RELEASE_WEBHOOK_URL="https://webhook",
        METACI_CHANGE_CASE_URL_TEMPLATE="{case_id}",
        METACI_RELEASE_WEBHOOK_ISSUER="MetaCI",
        METACI_RELEASE_WEBHOOK_AUTH_KEY="test",
    )
    mocked_responses.add(
        "POST",
        "https://webhook/case/2/submit",
        json={"success": True, "id": "2"},
    )

    project_config = Mock(project__package__name="Test Package")
    project_config.get_version_for_tag.return_value = "1.0"
    release = ReleaseFactory()
    release.change_case_link = "2"
    send_submit_webhook(release, "INFRA.instance1")
    assert len(mocked_responses.calls) == 1


def test_send_submit_webhook__disabled(mocked_responses):
    send_submit_webhook(None, None)
    assert len(mocked_responses.calls) == 0


def test_send_submit_webhook__error(mocked_responses, mocker, transactional_db):
    mocker.patch(
        "metaci.release.utils.settings",
        METACI_RELEASE_WEBHOOK_URL="https://webhook",
        METACI_RELEASE_WEBHOOK_ISSUER="MetaCI",
        METACI_RELEASE_WEBHOOK_AUTH_KEY="test",
    )
    mocked_responses.add(
        "POST",
        "https://webhook/case/None/submit",
        json={
            "success": False,
            "errors": ["Error submitting change case."],
        },
    )

    with pytest.raises(Exception):
        send_submit_webhook(ReleaseFactory(), "INFRA.instance1")
