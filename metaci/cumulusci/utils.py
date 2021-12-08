from typing import List

from metaci.cumulusci.models import OrgPool


def transform_org_pool_frozen_steps(pool: OrgPool) -> List[dict]:
    """Create an options dict for an invocation of `update_dependencies`
    based on the frozen steps stored on the org pool."""
    frozen_steps = [
        s
        for s in pool.frozen_steps
        if s["task_class"] == "cumulusci.tasks.salesforce.UpdateDependencies"
    ]
    options = frozen_steps[0]["task_config"]["options"]

    for step in frozen_steps[1:]:
        options["dependencies"].extend(step["task_config"]["options"]["dependencies"])

    return options
