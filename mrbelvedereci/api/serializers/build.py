from rest_framework import serializers
from mrbelvedereci.api.serializers.cumulusci import OrgSerializer
from mrbelvedereci.api.serializers.cumulusci import ScratchOrgInstanceSerializer
from mrbelvedereci.api.serializers.repository import BranchSerializer
from mrbelvedereci.api.serializers.repository import RepositorySerializer
from mrbelvedereci.api.serializers.plan import PlanSerializer
from mrbelvedereci.build.models import Build
from mrbelvedereci.build.models import BuildFlow
from mrbelvedereci.build.models import Rebuild
from mrbelvedereci.cumulusci.models import Org
from mrbelvedereci.plan.models import Plan
from mrbelvedereci.repository.models import Branch
from mrbelvedereci.repository.models import Repository

class BuildFlowSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = BuildFlow
        fields = (
            'id',
            'build',
            'error_message',
            'exception',
            'flow',
            'log',
            'rebuild',
            'status',
            'tests_fail',
            'tests_pass',
            'tests_total',
            'time_end',
            'time_queue',
            'time_start',
        )

build_flow_related_fields = list(BuildFlowSerializer.Meta.fields)
build_flow_related_fields.remove('log')
class BuildFlowRelatedSerializer(BuildFlowSerializer):
    class Meta(BuildFlowSerializer.Meta):
        fields = build_flow_related_fields

        
class RebuildSerializer(serializers.HyperlinkedModelSerializer):
    org_instance = ScratchOrgInstanceSerializer(read_only=True)
    class Meta:
        model = Rebuild
        fields = (
            'id',
            'build',
            'error_message',
            'exception',
            'org_instance',
            'status',
            'user',
            'time_end',
            'time_queue',
            'time_start',
        )

# mrbelvedereci.build Models
class BuildSerializer(serializers.HyperlinkedModelSerializer):
    branch = BranchSerializer(read_only=True)
    branch_id = serializers.PrimaryKeyRelatedField(
        queryset=Branch.objects.all(),
        source='branch',
        write_only=True
    )
    flows = BuildFlowRelatedSerializer(many=True, read_only=True)
    org = OrgSerializer(read_only=True)
    org_id = serializers.PrimaryKeyRelatedField(
        queryset=Org.objects.all(),
        source='org',
        write_only=True
    )
    org_instance = ScratchOrgInstanceSerializer(read_only=True)
    plan = PlanSerializer(read_only=True)
    plan_id = serializers.PrimaryKeyRelatedField(
        queryset=Plan.objects.all(),
        source='plan',
        write_only=True
    )
    repo = RepositorySerializer(read_only=True)
    repo_id = serializers.PrimaryKeyRelatedField(
        queryset=Repository.objects.all(),
        source='repo',
        write_only=True
    )
    class Meta:
        model = Build
        fields = (
            'id',
            'branch',
            'branch_id',
            'commit',
            'commit_message',
            'current_rebuild',
            'exception',
            'error_message',
            'flows',
            'log',
            'org',
            'org_id',
            'org_instance',
            'plan',
            'plan_id',
            'pr',
            'repo',
            'repo_id',
            'status',
            'tag',
            'time_end',
            'time_queue',
            'time_start',
        )
