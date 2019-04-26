import factory
import factory.fuzzy

import numbers
import random
import datetime


from metaci.plan.models import Plan, PlanRepository
from metaci.testresults.models import (
    TestResult,
    TestMethod,
    TestClass,
    TestResultPerfWeeklySummary,
)
from metaci.build.models import BuildFlow, Build, BUILD_STATUSES, BUILD_FLOW_STATUSES
from metaci.repository.models import Branch, Repository

from metaci.users.models import User

BUILD_STATUS_NAMES = (
    tuple(name for (name, label) in BUILD_STATUSES) + ("success",) * 7
)  # weighted towards success!
BUILD_FLOW_STATUS_NAMES = (name for (name, label) in BUILD_FLOW_STATUSES)

rand = random.Random()
rand.seed("limeandromeda")

factory.random.reseed_random("TOtaLLY RaNdOM")


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
        lambda a: (getattr(a, "name_prefix", None) or prefix or "")
        + factory.Faker("word").generate({})
    )


class PlanFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Plan
        exclude = ("name_prefix",)

    name_prefix = "Plan"
    name = fake_name()


class RepositoryFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Repository
        exclude = ("name_prefix",)

    name = fake_name()

    github_id = 1234
    name_prefix = "Repo_"
    owner = factory.fuzzy.FuzzyChoice(["SFDO", "SFDC", "Partner1", "Partner2"])


class PlanRepositoryFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = PlanRepository

    plan = factory.LazyAttribute(lambda x: rand.choice(Plan.objects.all()))
    repo = factory.SubFactory(RepositoryFactory)


class BranchFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Branch

    name = factory.fuzzy.FuzzyChoice(["master", "branch1", "branch2"])

    @factory.post_generation
    def postgen(obj, create, extracted, **kwargs):
        if not obj.repo:
            obj.repo = rand.choice(Repository.objects.all())
            obj.save()


class BuildFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Build

    planrepo = factory.SubFactory(PlanRepositoryFactory)
    plan = factory.LazyAttribute(lambda build: build.planrepo.plan)
    repo = factory.LazyAttribute(lambda build: build.planrepo.repo)
    branch = factory.LazyAttribute(
        lambda build: BranchFactory(repo=build.planrepo.repo)
    )
    status = factory.fuzzy.FuzzyChoice(BUILD_STATUS_NAMES)


class BuildFlowFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = BuildFlow

    tests_total = 1
    build = factory.SubFactory(BuildFactory)

    flow = factory.fuzzy.FuzzyChoice(["rida", "andebb", "ttank", "tleft"])
    status = factory.fuzzy.FuzzyChoice(BUILD_FLOW_STATUS_NAMES)
    time_end = (
        datetime.datetime.utcnow()
        .replace(tzinfo=datetime.timezone.utc)
        .isoformat()
        .split("T")[0]
    )


class TestClassFactory(factory.django.DjangoModelFactory):
    __test__ = False  # PyTest is confused by the classname

    class Meta:
        model = TestClass
        exclude = ("name_prefix",)

    name_prefix = "Test_"
    repo = factory.LazyAttribute(lambda x: rand.choice(Repository.objects.all()))
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
            obj._target_success_pct = rand.random() * 100
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
        success = rand.random() * 100 < result.method._target_success_pct
        if success:
            return "success"
        else:
            return rand.choice(["CompileFail", "Fail", "Skip"])

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
