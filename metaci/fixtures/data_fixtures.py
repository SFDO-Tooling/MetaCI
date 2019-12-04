import pytest

from metaci.conftest import (
    BuildFactory,
    BuildFlowFactory,
    PlanFactory,
    PlanRepositoryFactory,
    RepositoryFactory,
    StaffSuperuserFactory,
    TestClassFactory,
    TestMethodFactory,
    TestResultFactory,
    UserFactory,
)

"""Common data fixtures"""


@pytest.fixture
def user():
    """Create and return a non-superuser"""
    return UserFactory()


@pytest.fixture
def superuser():
    """Create and return a superuser"""
    return StaffSuperuserFactory()


@pytest.fixture
def data():
    """Creates a lot of interconnected test data"""
    data = {}
    data["repo"] = RepositoryFactory()
    data["plan"] = PlanFactory()
    data["planrepo"] = PlanRepositoryFactory(plan=data["plan"], repo=data["repo"])
    data["build"] = BuildFactory(planrepo=data["planrepo"])
    data["buildflow"] = BuildFlowFactory(build=data["build"], flow="flow-one")

    data["testclass"] = TestClassFactory(repo=data["repo"])
    data["testclass"].test_type = "Apex"
    data["testclass"].save()

    data["testmethod"] = TestMethodFactory(testclass=data["testclass"])
    data["testmethod"].test_dashboard = True
    data["testmethod"].save()

    data["testresult"] = TestResultFactory(
        method=data["testmethod"], build_flow=data["buildflow"]
    )
    data["testresult"].build = data["build"]
    data["testresult"].save()

    return data
