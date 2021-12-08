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
from metaci.cumulusci.utils import transform_org_pool_frozen_steps


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
        frozen_steps = [
            {
                "name": "Install sfdobase 1.0",
                "kind": "managed",
                "is_required": True,
                "path": "customer_org.update_dependencies.1",
                "step_num": "1/1.1",
                "task_class": "cumulusci.tasks.salesforce.UpdateDependencies",
                "task_config": {
                    "options": {
                        "packages_only": False,
                        "dependencies": [{"namespace": "sfdobase", "version": "1.0"}],
                    },
                    "checks": [],
                },
                "source": None,
            }
        ]
        org_pool = OrgPool(
            minimum_org_count=3,
            minimum_lifespan=7,
            repository=repo,
            org_shape=org,
            frozen_steps=frozen_steps,
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


def test_transform_org_pool_frozen_steps():
    frozen_steps = [
        {
            "name": "Install sfdobase 1.0",
            "kind": "managed",
            "is_required": True,
            "path": "customer_org.update_dependencies.1",
            "step_num": "1/1.1",
            "task_class": "cumulusci.tasks.salesforce.UpdateDependencies",
            "task_config": {
                "options": {
                    "packages_only": False,
                    "dependencies": [{"namespace": "sfdobase", "version": "1.0"}],
                },
                "checks": [],
            },
            "source": None,
        },
        {
            "name": "Install PMM 1.0",
            "kind": "managed",
            "is_required": True,
            "path": "customer_org.update_dependencies.1",
            "step_num": "1/1.1",
            "task_class": "cumulusci.tasks.salesforce.UpdateDependencies",
            "task_config": {
                "options": {
                    "packages_only": True,
                    "dependencies": [{"namespace": "pmm", "version": "1.0"}],
                },
                "checks": [],
            },
            "source": None,
        },
    ]

    pool = OrgPool(frozen_steps=frozen_steps)

    assert transform_org_pool_frozen_steps(pool) == {
        "packages_only": False,
        "dependencies": [
            {"namespace": "sfdobase", "version": "1.0"},
            {"namespace": "pmm", "version": "1.0"},
        ],
    }
