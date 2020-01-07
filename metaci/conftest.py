import os

import pytest

from metaci.fixtures.data_fixtures import data, superuser, user
from metaci.fixtures.factories import (
    BranchFactory,
    BuildFactory,
    BuildFlowFactory,
    FlowTaskFactory,
    OrgFactory,
    PlanFactory,
    PlanRepositoryFactory,
    PlanScheduleFactory,
    RebuildFactory,
    RepositoryFactory,
    ScratchOrgInstanceFactory,
    StaffSuperuserFactory,
    TestClassFactory,
    TestMethodFactory,
    TestResultFactory,
    UserFactory,
)
from metaci.fixtures.util import client


@pytest.fixture(autouse=True)
def restore_cwd():
    """Restore current directory after each test."""
    cwd = os.getcwd()
    try:
        yield
    finally:
        os.chdir(cwd)
