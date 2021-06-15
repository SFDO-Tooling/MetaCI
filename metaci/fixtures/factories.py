import numbers
import random

import factory
import factory.fuzzy
from django.utils import timezone
from faker import Faker

from metaci.build.models import (
    BUILD_FLOW_STATUSES,
    BUILD_STATUSES,
    Build,
    BuildFlow,
    FlowTask,
    Rebuild,
)
from metaci.cumulusci.models import Org, ScratchOrgInstance
from metaci.plan.models import Plan, PlanRepository, PlanSchedule
from metaci.release.models import ChangeCaseTemplate, Release
from metaci.repository.models import Branch, Repository
from metaci.testresults.models import (
    TestClass,
    TestMethod,
    TestResult,
    TestResultPerfWeeklySummary,
)
from metaci.users.models import User

BUILD_STATUS_NAMES = (
    tuple(name for (name, label) in BUILD_STATUSES) + ("success",) * 7
)  # weighted towards success!
BUILD_FLOW_STATUS_NAMES = (name for (name, label) in BUILD_FLOW_STATUSES)

fake = Faker()


def do_logs():
    """Call this function at the module level to get more insight
    into what FactoryBoy is doing under the covers."""
    import logging

    logger = logging.getLogger("factory")
    logger.addHandler(logging.StreamHandler())
    logger.setLevel(logging.DEBUG)


def fake_name(prefix=None):
    """Generate a fake name with a certain prefix. You can push the name_prefix
    from outside of the factory if you have a preference when you instantiate
    the class."""
    return factory.LazyAttribute(
        lambda a: (getattr(a, "name_prefix", None) or prefix or "") + fake.word()
    )


class PlanFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Plan
        exclude = ("name_prefix",)

    name_prefix = "Plan"
    name = fake_name()
    role = "test"


class RepositoryFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Repository
        exclude = ("name_prefix",)

    name = fake_name()

    github_id = 1234
    name_prefix = "Repo_"
    owner = factory.fuzzy.FuzzyChoice(["SFDO", "SFDC", "Partner1", "Partner2"])


class OrgFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Org

    repo = factory.SubFactory(RepositoryFactory)
    json = {}


class ScratchOrgInstanceFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = ScratchOrgInstance

    org = factory.SubFactory(OrgFactory)
    json = {}


class PlanRepositoryFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = PlanRepository

    plan = factory.SubFactory(PlanFactory)
    repo = factory.SubFactory(RepositoryFactory)


class BranchFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Branch

    name = factory.fuzzy.FuzzyChoice(["main", "branch1", "branch2"])
    repo = factory.SubFactory(RepositoryFactory)


class BuildFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Build

    planrepo = factory.SubFactory(PlanRepositoryFactory)
    plan = factory.SelfAttribute("planrepo.plan")
    repo = factory.SelfAttribute("planrepo.repo")
    branch = factory.LazyAttribute(
        lambda build: BranchFactory(repo=build.planrepo.repo)
    )
    status = factory.fuzzy.FuzzyChoice(BUILD_STATUS_NAMES)
    commit = str(random.getrandbits(128))


class BuildFlowFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = BuildFlow

    tests_total = 1
    build = factory.SubFactory(BuildFactory)

    flow = factory.fuzzy.FuzzyChoice(["rida", "andebb", "ttank", "tleft"])
    status = factory.fuzzy.FuzzyChoice(BUILD_FLOW_STATUS_NAMES)
    time_end = timezone.now()


class TestClassFactory(factory.django.DjangoModelFactory):
    __test__ = False  # PyTest is confused by the classname

    class Meta:
        model = TestClass
        exclude = ("name_prefix",)

    name_prefix = "Test_"
    repo = factory.Sequence(
        lambda x: Repository.objects.all()[x % len(Repository.objects.all())]
    )
    name = fake_name()


class TestMethodFactory(factory.django.DjangoModelFactory):
    __test__ = False  # PyTest is confused by the classname

    class Meta:
        model = TestMethod
        exclude = ("name_prefix",)

    name_prefix = "Test_"
    testclass = factory.SubFactory(TestClassFactory)
    name = fake_name()

    @factory.post_generation
    def _target_success_setter(obj, create, extracted=None, **kwargs):
        if isinstance(extracted, numbers.Number):
            obj._target_success_pct = extracted
        else:
            obj._target_success_pct = (ord(obj.name[0].lower()) - ord("a")) * 4
        obj._runs = 0
        obj.save()


class TestResultFactory(factory.django.DjangoModelFactory):
    __test__ = False  # PyTest is confused by the classname

    class Meta:
        model = TestResult
        exclude = ("target_success_rate",)

    build_flow = factory.SubFactory(BuildFlowFactory)
    method = factory.SubFactory(TestMethodFactory)
    duration = factory.fuzzy.FuzzyFloat(2, 10000)

    @factory.LazyAttribute
    def outcome(result):
        return ["Pass", "Pass", "Pass", "CompileFail", "Fail", "Skip"][
            result.method._runs % 6
        ]

    @factory.post_generation
    def summarize(obj, create, extracted, **kwargs):
        TestResultPerfWeeklySummary.summarize_week(obj.build_flow.time_end)


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User
        django_get_or_create = ("username",)

    email = factory.Sequence("user_{}@example.com".format)
    username = factory.Sequence("user_{}@example.com".format)
    password = factory.PostGenerationMethodCall("set_password", "foobar")


class StaffSuperuserFactory(UserFactory):
    is_staff = True
    is_superuser = True


class PlanScheduleFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = PlanSchedule

    branch = factory.SubFactory(BranchFactory)
    plan = factory.SubFactory(PlanFactory)


class FlowTaskFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = FlowTask

    build_flow = factory.SubFactory(BuildFlowFactory)
    stepnum = factory.Sequence(lambda n: f"{n}")
    path = factory.Sequence(lambda n: f"flow_1.task_{n}")


class RebuildFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Rebuild

    user = factory.SubFactory(UserFactory)
    build = factory.SubFactory(BuildFactory)
    org_instance = factory.SubFactory(ScratchOrgInstanceFactory)
    status = factory.fuzzy.FuzzyChoice(BUILD_STATUS_NAMES)


class ChangeCaseTemplateFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = ChangeCaseTemplate

    case_template_id = "1"


class ReleaseFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Release

    change_case_template = factory.SubFactory(ChangeCaseTemplateFactory)
    repo = factory.SubFactory(RepositoryFactory)
    git_tag = "release/1.0"
