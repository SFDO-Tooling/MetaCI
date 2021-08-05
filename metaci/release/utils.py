import logging
import re
import urllib.parse
from calendar import timegm
from datetime import datetime

import jwt
import requests
from django.conf import settings
from django.db import transaction
from django.utils.dateparse import parse_date

logger = logging.getLogger(__name__)


def implementation_payload(role, config_item, infra_type, release):
    if role and config_item and release and infra_type:
        implementation_step = release.implementation_steps.get(plan__role=role)
        return {
            "description": role,
            "owner": settings.GUS_BUS_OWNER_ID,
            "start_time": implementation_step.start_time.astimezone(None).isoformat(),
            "end_time": implementation_step.stop_time.astimezone(None).isoformat(),
            "configuration_item": config_item,
            "infrastructure_type": infra_type,
            "implementation_steps": role,
        }
    raise Exception("Please check your plan's role and org's configuration item.")


def jwt_for_webhook():
    return jwt.encode(
        {
            "iss": settings.METACI_RELEASE_WEBHOOK_ISSUER,
            "exp": timegm(datetime.utcnow().utctimetuple()),
        },
        settings.METACI_RELEASE_WEBHOOK_AUTH_KEY,
        algorithm="HS256",
    )


def update_release_from_github(release, repo_api=None):
    if not repo_api:
        repo_api = release.repo.get_github_api()
    if not release.git_tag:
        logger.info("Cannot update release, no git_tag specified")
        return
    ref = repo_api.ref(f"tags/{release.git_tag}")
    if not ref:
        logger.info(
            f"Cannot update release, ref tags/{release.git_tag} not found in Github"
        )
        return
    gh_release = repo_api.release_by_tag_name(release.git_tag)
    release.status = "published"
    release.version_name = gh_release.name
    release.version_number = gh_release.name
    release.github_release = gh_release.html_url
    release.release_creation_date = gh_release.created_at
    release.created_from_commit = ref.object.sha
    sandbox_date = re.findall(
        r"^Sandbox orgs: (20[\d][\d]-[\d][\d]-[\d][\d])", gh_release.body
    )
    if sandbox_date:
        release.sandbox_push_date = parse_date(sandbox_date[0], "%Y-%m-%d")

    prod_date = re.findall(
        r"^Production orgs: (20[\d][\d]-[\d][\d]-[\d][\d])", gh_release.body
    )
    if prod_date:
        release.production_push_date = parse_date(prod_date[0], "%Y-%m-%d")

    package_version_id = re.findall(r"(04t[\w]{15,18})", gh_release.body)
    if package_version_id:
        release.package_version_id = package_version_id[0]

    trialforce_id = re.findall(r"^(0TT[\w]{15,18})", gh_release.body)
    if trialforce_id:
        release.trialforce_id = trialforce_id[0]

    return release


def send_release_webhook(release, config_item=None):
    if release is None or not settings.METACI_RELEASE_WEBHOOK_URL:
        return  # should we better error handle this?
    logger.info(
        f"Sending release webhook for {release} to {settings.METACI_RELEASE_WEBHOOK_URL}"
    )
    tag = release.git_tag
    steps = []
    if config_item and settings.GUS_BUS_OWNER_ID:
        implementation_steps = release.implementation_steps.all()
        steps = [
            implementation_payload(
                implementation_step.plan.role, config_item, "Release Deploy", release
            )
            for implementation_step in implementation_steps
        ]
    payload = {
        "case_template_id": release.change_case_template.case_template_id,
        "package_name": release.repo.name,  # Need to figure out.
        "version": release.version_number,
        "release_url": f"{release.repo.url}/releases/tag/{urllib.parse.quote(tag)}",
        "steps": steps,
    }
    token = jwt_for_webhook()
    response = requests.post(
        f"{settings.METACI_RELEASE_WEBHOOK_URL}/release/",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )
    result = response.json()

    if result["success"]:
        with transaction.atomic():
            if (
                "implementationSteps" in result
                and len(result["implementationSteps"]) > 0
            ):
                for step_model, step_result in zip(
                    implementation_steps, result["implementationSteps"]
                ):
                    step_model.external_id = step_result
                    step_model.save()
            case_id = result["id"]
            case_url = settings.METACI_CHANGE_CASE_URL_TEMPLATE.format(case_id=case_id)
            release.change_case_link = case_url
            release.save()
    else:
        raise Exception("\n".join(err["message"] for err in result["errors"]))


def send_submit_webhook(release, config_item=None):
    if (
        release is None
        or not settings.METACI_RELEASE_WEBHOOK_URL
        or not settings.GUS_BUS_OWNER_ID
        or not config_item
    ):
        return
    logger.info(
        f"Sending submit webhook for {release} to {settings.METACI_RELEASE_WEBHOOK_URL}"
    )

    payload = {"case_id": release.change_case_link}
    token = jwt_for_webhook()
    response = requests.post(
        f"{settings.METACI_RELEASE_WEBHOOK_URL}/case/{release.change_case_link}/submit",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )
    result = response.json()

    if (
        "results" in result
        and len(result["results"]) > 0
        and result["results"][0]["success"]
    ):
        return
    else:
        raise Exception("\n".join(err for err in result["errors"]))


def send_start_webhook(release, role, config_item):
    if release is None or not settings.METACI_RELEASE_WEBHOOK_URL:
        return
    if not config_item:
        logger.warning(
            "Error sending start webhook, please include a configuration item, which can be defined on the org object."
        )
        return
    logger.info(
        f"Sending start webhook for {release} to {settings.METACI_RELEASE_WEBHOOK_URL}"
    )
    implementation_step_id = release.implementation_steps.get(
        plan__role=role
    ).external_id
    payload = {
        "implementation_step_id": f"{implementation_step_id}",
    }
    token = jwt_for_webhook()
    response = requests.post(
        f"{settings.METACI_RELEASE_WEBHOOK_URL}/implementation/{implementation_step_id}/start",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )
    result = response.json()
    if (
        "results" in result
        and len(result["results"]) > 0
        and result["results"][0]["success"]
    ):
        logger.info(
            f"Successfully started implementation_step: {implementation_step_id}"
        )
        return
    else:
        msg = "\n".join(err for err in result["errors"])
        raise Exception(f"Error while sending implementation start step webhook: {msg}")


def send_stop_webhook(release, role, config_item, status):
    if release is None or not settings.METACI_RELEASE_WEBHOOK_URL:
        return
    if not config_item:
        logger.warning(
            "Error sending stop webhook, please include a configuration item, which can be defined on the org object."
        )
        return
    logger.info(
        f"Sending stop webhook for {release} to {settings.METACI_RELEASE_WEBHOOK_URL}"
    )
    implementation_step_id = release.implementation_steps.get(
        plan__role=role
    ).external_id
    payload = {
        "implementation_step_id": f"{implementation_step_id}",
        "status": status,
    }
    token = jwt_for_webhook()
    response = requests.post(
        f"{settings.METACI_RELEASE_WEBHOOK_URL}/implementation/{implementation_step_id}/stop?status={status}",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )
    result = response.json()
    if (
        "results" in result
        and len(result["results"]) > 0
        and result["results"][0]["success"]
    ):
        logger.info(
            f"Successfully stopped implementation_step: {implementation_step_id}"
        )
        return
    else:
        msg = "\n".join(err for err in result["errors"])
        raise Exception(f"Error while sending implementation stop step webhook: {msg}")
