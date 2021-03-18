from unittest.mock import Mock

import pytest

from ...fixtures.factories import ReleaseFactory
from ..utils import send_release_webhook


def test_send_release_webhook(mocked_responses, mocker, transactional_db):
    mocker.patch(
        "metaci.release.utils.settings",
        METACI_RELEASE_WEBHOOK_URL="https://webhook",
        METACI_CHANGE_CASE_URL_TEMPLATE="{case_id}",
        METACI_RELEASE_WEBHOOK_ISSUER="MetaCI",
        METACI_RELEASE_WEBHOOK_AUTH_KEY="test",
    )
    mocked_responses.add(
        "POST", "https://webhook/release/", json={"success": True, "id": "2"}
    )

    project_config = Mock(project__package__name="Test Package")
    project_config.get_version_for_tag.return_value = "1.0"
    release = ReleaseFactory()

    send_release_webhook(project_config, release, "INFRA.instance1")

    assert release.change_case_link == "2"


def test_send_release_webhook__disabled(mocked_responses):
    send_release_webhook(None, None, None)
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
        send_release_webhook(project_config, release, "INFRA.instance1")
