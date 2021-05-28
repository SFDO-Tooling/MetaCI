import os

import pytest
import responses

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
    ReleaseFactory,
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


@pytest.fixture()
def mocked_responses():
    with responses.RequestsMock() as mocked:
        yield mocked
