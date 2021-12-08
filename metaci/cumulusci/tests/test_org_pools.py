import pytest

import metaci.cumulusci.handlers
import metaci.cumulusci.signals  # noqa: F401
from metaci.build.signals import build_complete
from metaci.conftest import (
    OrgFactory,
    PlanFactory,
    RepositoryFactory,
    ScratchOrgInstanceFactory,
)
from metaci.cumulusci.models import OrgPool
from metaci.cumulusci.signals import org_claimed


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
        org_pool = OrgPool(
            minimum_org_count=3,
            minimum_lifespan=7,
            repository=repo,
            org_shape=org,
            dependencies=dependencies,
        )
        org_pool.save()
        assert org_pool.builds.count() == 3
        for build in org_pool.builds.all():
            assert build.plan.role == "pool_org"
            org_instance = ScratchOrgInstanceFactory()
            build.org_instance = org_instance
            build.save()
            build_complete.send(sender="sender", build=build, status="success")
        org_pool.refresh_from_db()
        assert org_pool.pooled_orgs.count() == 3
        org_claimed.send(sender="sender", org_pool=org_pool)
        assert org_pool.builds.count() == 4
