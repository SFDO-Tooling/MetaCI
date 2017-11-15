from rest_framework import serializers
from django.contrib.auth import get_user_model
from metaci.api.serializers.repository import RepositorySerializer
from metaci.cumulusci.models import Org
from metaci.cumulusci import choices
from metaci.cumulusci.models import ScratchOrgInstance
from metaci.cumulusci.models import Service
from metaci.repository.models import Repository

class OrgSerializer(serializers.HyperlinkedModelSerializer):
    repo = RepositorySerializer(read_only=True)
    repo_id = serializers.PrimaryKeyRelatedField(
        queryset=Repository.objects.all(),
        source='repo',
        write_only=True
    )
    class Meta:
        model = Org
        fields = (
            'id',
            'json',
            'name',
            'repo',
            'repo_id',
            'scratch',
            'org_type',
            'org_id'
        )

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = get_user_model()
        fields = ('id','username')

class RegisteredOrgSerializer(serializers.HyperlinkedModelSerializer):
    repo = RepositorySerializer(read_only=True)
    repo_id = serializers.PrimaryKeyRelatedField(
        queryset=Repository.objects.all(),
        source='repo',
        write_only=True
    )
    owner = UserSerializer(read_only=True)
    owner_id = serializers.PrimaryKeyRelatedField(
        queryset=get_user_model().objects.all(),
        source='owner',
        write_only=True
    )
    class Meta:
        model = Org
        fields = (
            'id',
            'name',
            'repo', 'repo_id',
            'org_id', 'org_type', 'release_cycle',
            'description', 'owner', 'owner_id',
            'last_deploy', 'last_deploy_version'
        )

    def save(self, *args, **kwargs):
        self.validated_data['supertype'] = choices.SUPERTYPE_REGISTERED
        super(RegisteredOrgSerializer, self).save(*args, **kwargs)

    
class ScratchOrgInstanceSerializer(serializers.HyperlinkedModelSerializer):
    org = OrgSerializer(read_only=True)
    org_id = serializers.PrimaryKeyRelatedField(
        queryset=Org.ci_orgs.all(),
        source='org',
        write_only=True
    )
    class Meta:
        model = ScratchOrgInstance
        fields = (
            'id',
            'build',
            'deleted',
            'org',
            'org_id',
            'sf_org_id',
            'time_created',
            'time_deleted',
            'username',
        )
        
class ServiceSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Service
        fields = (
            'id',
            'name',
            'json',
        )
