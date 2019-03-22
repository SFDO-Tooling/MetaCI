import factory
import factory.fuzzy

from metaci.plan.models import Plan, PlanRepository
from metaci.testresults.models import TestResult, TestMethod, TestClass
from metaci.build.models import BuildFlow, Build
from metaci.repository.models import Branch, Repository

from metaci.users.models import User


class PlanFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Plan


class RepositoryFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Repository

    github_id = 1234


class PlanRepositoryFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = PlanRepository

    plan = factory.SubFactory(PlanFactory)
    repo = factory.SubFactory(RepositoryFactory)


class BranchFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Branch


class BuildFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Build

    plan = factory.SubFactory(PlanFactory)
    repo = factory.SubFactory(RepositoryFactory)


class BuildFlowFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = BuildFlow

    tests_total = 5
    build = factory.SubFactory(BuildFactory)
    flow = "rida"


class TestClassFactory(factory.django.DjangoModelFactory):
    __test__ = False  # PyTest is confused by the classname

    class Meta:
        model = TestClass

    repo = factory.SubFactory(RepositoryFactory)


class TestMethodFactory(factory.django.DjangoModelFactory):
    __test__ = False  # PyTest is confused by the classname

    class Meta:
        model = TestMethod

    testclass = factory.SubFactory(TestClassFactory)
    name = "GenericMethod"


class TestResultFactory(factory.django.DjangoModelFactory):
    __test__ = False  # PyTest is confused by the classname

    class Meta:
        model = TestResult

    build_flow = factory.SubFactory(BuildFlowFactory)
    method = factory.SubFactory(TestMethodFactory)
    duration = 5


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User
        django_get_or_create = ("username",)

    email = factory.Sequence("user_{}@example.com".format)
    username = factory.Sequence("user_{}@example.com".format)
    password = factory.PostGenerationMethodCall("set_password", "foobar")
    # socialaccount_set = factory.RelatedFactory(SocialAccountFactory, "user")


class StaffSuperuserFactory(UserFactory):
    is_staff = True
    is_superuser = True
