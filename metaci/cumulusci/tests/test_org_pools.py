import pytest

from metaci.conftest import (
    PlanFactory,
    RepositoryFactory,
    OrgFactory,
    ScratchOrgInstanceFactory,
)
from metaci.cumulusci.models import OrgPool
import metaci.cumulusci.signals
import metaci.cumulusci.handlers
from metaci.build.signals import build_complete


class TestOrgPools:
    @pytest.mark.django_db
    def test_fill_pool(self):
        repo = RepositoryFactory(
            name="CumulusCI-Test",
            owner="SFDO-Tooling",
            url="https://github.com/SFDO-Tooling/CumulusCI-Test",
        )
        org = OrgFactory(name="myorg", repo=repo, scratch=False)
        _ = PlanFactory(role="pool_org")
        dependencies = [{"version": "1", "namespace": "foo"}]
        pool = OrgPool(
            minimum_org_count=3,
            minimum_lifespan=7,
            repository=repo,
            org_shape=org,
            dependencies=dependencies,
        )
        pool.save()
        assert pool.builds.count() == 3
        for build in pool.builds.all():
            assert build.plan.role == "pool_org"
            org_instance = ScratchOrgInstanceFactory()
            build.org_instance = org_instance
            build.save()
            build_complete.send(sender="sender", build=build, status="success")
        pool.refresh_from_db()
        assert pool.pooled_orgs.count() == 3
