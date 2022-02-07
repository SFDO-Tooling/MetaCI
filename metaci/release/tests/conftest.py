from unittest import mock

import pytest
from django.conf import settings

from metaci.build.models import BUILD_STATUSES, Build, BuildFlow, FlowTask
from metaci.fixtures.factories import (BuildFactory, BuildFlowFactory,
                                       FlowTaskFactory, ReleaseCohortFactory,
                                       ReleaseFactory)
from metaci.release.models import Release, ReleaseCohort


@pytest.fixture
def dependent_releases():
    def inner():
        rc = ReleaseCohortFactory(dependency_graph={})
        top = ReleaseFactory(
            repo__url="https://github.com/example/top",
            release_cohort=rc,
            status=Release.STATUS.draft,
            created_from_commit="abc",
        )
        left = ReleaseFactory(
            repo__url="https://github.com/example/left",
            release_cohort=rc,
            status=Release.STATUS.draft,
            created_from_commit="ghi",
        )
        right = ReleaseFactory(
            repo__url="https://github.com/example/right",
            release_cohort=rc,
            status=Release.STATUS.draft,
            created_from_commit="jkl",
        )
        separate = ReleaseFactory(
            repo__url="https://github.com/example/separate",
            release_cohort=rc,
            status=Release.STATUS.draft,
            created_from_commit="mno",
        )
        rc.dependency_graph = {
            left.repo.url: [top.repo.url],
            right.repo.url: [top.repo.url, left.repo.url],
        }
        rc.save()

        return (rc, top, left, right, separate)

    return inner


@pytest.fixture
def dependent_releases_with_builds(dependent_releases):
    def inner():
        rc, top, left, right, separate = dependent_releases()
        rc.status = ReleaseCohort.STATUS.completed
        rc.save()
        top.status = (
            left.status
        ) = right.status = separate.status = Release.STATUS.completed

        build_top = BuildFactory(
            release=top, planrepo__plan__role="release", status=BUILD_STATUSES.success
        )
        build_flow_top = BuildFlowFactory(build=build_top)
        flow_task_top = FlowTaskFactory(
            class_path="cumulusci.tasks.salesforce.PackageUpload",
            build_flow=build_flow_top,
            return_values={
                "version_id": "04t000000000top",
                "package_id": "033000000000top",
            },
        )

        build_left = BuildFactory(
            release=left, planrepo__plan__role="release", status=BUILD_STATUSES.success
        )
        build_flow_left = BuildFlowFactory(build=build_left)
        flow_task_left = FlowTaskFactory(
            class_path="cumulusci.tasks.salesforce.PackageUpload",
            build_flow=build_flow_left,
            return_values={
                "version_id": "04t00000000left",
                "package_id": "03300000000left",
            },
        )

        build_right = BuildFactory(
            release=right, planrepo__plan__role="release", status=BUILD_STATUSES.success
        )
        build_flow_right = BuildFlowFactory(build=build_right)
        flow_task_right = FlowTaskFactory(
            class_path="cumulusci.tasks.salesforce.PackageUpload",
            build_flow=build_flow_right,
            return_values={
                "version_id": "04t0000000right",
                "package_id": "0330000000right",
            },
        )

        build_separate = BuildFactory(
            release=separate,
            planrepo__plan__role="release",
            status=BUILD_STATUSES.success,
        )
        build_flow_separate = BuildFlowFactory(build=build_separate)
        flow_task_separate = FlowTaskFactory(
            class_path="cumulusci.tasks.salesforce.PackageUpload",
            build_flow=build_flow_separate,
            return_values={
                "version_id": "04t0000separate",
                "package_id": "0330000separate",
            },
        )

        return (rc, top, left, right, separate)

    return inner


@pytest.fixture
def metapush_configured(settings):
    token = "TOKEN"
    endpoint = "https://metapush.example"

    settings.METAPUSH_AUTHENTICATION_TOKEN = token
    settings.METAPUSH_ENDPOINT_URL = endpoint

    return (endpoint, token)


@pytest.fixture
def metapush_not_configured(settings):
    settings.METAPUSH_AUTHENTICATION_TOKEN = None
    settings.METAPUSH_ENDPOINT_URL = None
