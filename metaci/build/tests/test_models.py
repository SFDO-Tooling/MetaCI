import os
from pathlib import Path
from unittest import mock

import pytest
from cumulusci.core.config import OrgConfig

from metaci.build.models import Build
from metaci.conftest import (
    BranchFactory,
    BuildFactory,
    BuildFlowFactory,
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

    @mock.patch("metaci.repository.models.Repository.github_api")
    @mock.patch("metaci.cumulusci.keychain.MetaCIProjectKeychain.get_org")
    def test_run(self, get_org, gh):
        # mock github zipball
        def archive(format, zip_content, ref):
            with open(Path(__file__).parent / "testproject.zip", "rb") as f:
                zip_content.write(f.read())

        gh.archive.side_effect = archive

        # mock org config
        org_config = OrgConfig({}, "test")
        org_config.refresh_oauth_token = mock.Mock()
        get_org.return_value = org_config

        build = BuildFactory()
        build.plan.flows = "test"

        try:
            build.run()
        finally:
            detach_logger(build)

        assert build.status == "success", build.log
        assert "Build flow test completed successfully" in build.log
        assert "running test flow" in build.flows.get().log

    def test_delete_org(self):
        build = BuildFactory()
        build.org_instance = ScratchOrgInstanceFactory(org__repo=build.repo)
        build.org_instance.delete_org = mock.Mock()
        org_config = OrgConfig({"scratch": True}, "dev")
        build.delete_org(org_config)
        build.org_instance.delete_org.assert_called_once()
        detach_logger(build)

    def test_delete_org__not_scratch(self):
        build = BuildFactory()
        build.org_instance = ScratchOrgInstanceFactory(org__repo=build.repo)
        build.org_instance.delete_org = mock.Mock()
        org_config = OrgConfig({}, "dev")
        build.delete_org(org_config)
        build.org_instance.delete_org.assert_not_called()
        detach_logger(build)

    def test_delete_org__keep_org(self):
        build = BuildFactory(keep_org=True)
        org = ScratchOrgInstanceFactory()
        org.delete_org = mock.Mock()
        build.org_instance = org
        org_config = OrgConfig({"scratch": True}, "dev")
        build.delete_org(org_config)
        org.delete_org.assert_not_called()
        detach_logger(build)

    def test_delete_org__keep_org_on_error(self):
        build = BuildFactory(status="error")
        build.plan.keep_org_on_error = True
        org = ScratchOrgInstanceFactory()
        org.delete_org = mock.Mock()
        build.org_instance = org
        org_config = OrgConfig({"scratch": True}, "dev")
        build.delete_org(org_config)
        org.delete_org.assert_not_called()
        detach_logger(build)

    def test_delete_org__keep_org_on_fail(self):
        build = BuildFactory(status="fail")
        build.plan.keep_org_on_fail = True
        org = ScratchOrgInstanceFactory()
        org.delete_org = mock.Mock()
        build.org_instance = org
        org_config = OrgConfig({"scratch": True}, "dev")
        build.delete_org(org_config)
        org.delete_org.assert_not_called()
        detach_logger(build)

    @mock.patch.dict(os.environ, clear=True)
    def test_no_worker_id(self):
        build = BuildFactory()
        assert not build.worker_id

    @mock.patch.dict(os.environ, {"DYNO": "faker.1"})
    def test_dyno_worker_id(self):
        build = BuildFactory()
        assert build.worker_id == "faker.1"

    def test_get_commit(self):
        build = BuildFactory()
        commit_sha = build.commit
        truncated_commit = build.get_commit()
        assert f"{commit_sha[:6]}..." == truncated_commit


@pytest.mark.django_db
class TestBuildFlow:
    def test_set_commit_status(self):
        build_flow = BuildFlowFactory()
        build_flow.build.plan.commit_status_template = "{{ 2 + 2 }}"
        build_flow.flow_instance = mock.Mock()
        build_flow.set_commit_status()
        assert build_flow.build.commit_status == "4"


def detach_logger(model):
    for handler in model.logger.handlers:
        model.logger.removeHandler(handler)
