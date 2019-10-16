import os
from unittest import mock
from unittest.mock import Mock

import pytest
from cumulusci.core.config import OrgConfig

from metaci.build.models import Build
from metaci.conftest import (
    BranchFactory,
    BuildFactory,
    PlanFactory,
    PlanRepositoryFactory,
    PlanScheduleFactory,
    RepositoryFactory,
    ScratchOrgInstanceFactory,
)


@pytest.mark.django_db
class TestBuild:
    def test_empty_build_init(self):
        Build()

    def test_scheduled_build_init(self):
        repo = RepositoryFactory()
        branch = BranchFactory(name="branch", repo=repo)
        schedule = PlanScheduleFactory(branch=branch)
        plan = PlanFactory()

        planrepo = PlanRepositoryFactory(plan=plan, repo=repo)

        build = Build(
            repo=branch.repo,
            plan=plan,
            branch=branch,
            commit="shashasha",
            schedule=schedule,
            build_type="scheduled",
        )
        assert build.planrepo == planrepo

    def test_planrepo_find_on_build_init(self):
        repo = RepositoryFactory()
        plan = PlanFactory()
        planrepo = PlanRepositoryFactory(plan=plan, repo=repo)

        build = Build(repo=repo, plan=plan)
        assert build.planrepo == planrepo

    def test_delete_org(self):
        build = BuildFactory()
        build.org_instance = ScratchOrgInstanceFactory(org__repo=build.repo)
        build.org_instance.delete_org = Mock()
        org_config = OrgConfig({"scratch": True}, "dev")
        build.delete_org(org_config)
        build.org_instance.delete_org.assert_called_once()
        detach_logger(build)

    def test_delete_org__not_scratch(self):
        build = BuildFactory()
        build.org_instance = ScratchOrgInstanceFactory(org__repo=build.repo)
        build.org_instance.delete_org = Mock()
        org_config = OrgConfig({}, "dev")
        build.delete_org(org_config)
        build.org_instance.delete_org.assert_not_called()
        detach_logger(build)

    def test_delete_org__keep_org(self):
        build = BuildFactory(keep_org=True)
        org = ScratchOrgInstanceFactory()
        org.delete_org = Mock()
        build.org_instance = org
        org_config = OrgConfig({"scratch": True}, "dev")
        build.delete_org(org_config)
        org.delete_org.assert_not_called()
        detach_logger(build)

    def test_delete_org__keep_org_on_error(self):
        build = BuildFactory(status="error")
        build.plan.keep_org_on_error = True
        org = ScratchOrgInstanceFactory()
        org.delete_org = Mock()
        build.org_instance = org
        org_config = OrgConfig({"scratch": True}, "dev")
        build.delete_org(org_config)
        org.delete_org.assert_not_called()
        detach_logger(build)

    def test_delete_org__keep_org_on_fail(self):
        build = BuildFactory(status="fail")
        build.plan.keep_org_on_fail = True
        org = ScratchOrgInstanceFactory()
        org.delete_org = Mock()
        build.org_instance = org
        org_config = OrgConfig({"scratch": True}, "dev")
        build.delete_org(org_config)
        org.delete_org.assert_not_called()
        detach_logger(build)

    def test_noop_worker_id(self):
        build = BuildFactory()
        assert not build.worker_id

    @mock.patch.dict(os.environ, {"DYNO": "faker.1"})
    def test_dyno_worker_id(self):
        build = BuildFactory()
        assert build.worker_id == "faker.1"


def detach_logger(model):
    for handler in model.logger.handlers:
        model.logger.removeHandler(handler)
