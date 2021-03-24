import json

from cumulusci.core.config import OrgConfig, ScratchOrgConfig, ServiceConfig
from cumulusci.core.exceptions import ServiceNotConfigured
from cumulusci.core.keychain import BaseProjectKeychain
from django.conf import settings
from django.core.serializers.json import DjangoJSONEncoder

from metaci.cumulusci.logger import init_logger
from metaci.cumulusci.models import Org, ScratchOrgInstance, Service


class MetaCIProjectKeychain(BaseProjectKeychain):
    def __init__(self, project_config, key, build):
        self.build = build
        super(MetaCIProjectKeychain, self).__init__(project_config, key)

    def _load_keychain_services(self):
        for key, value in settings.__dict__["_wrapped"].__dict__.items():
            if key.startswith("CUMULUSCI_SERVICE_"):
                print(f"%%% DEBUG %%%: {key[len('CUMULUSCI_SERVICE_') :]}")
                self.services[key[len("CUMULUSCI_SERVICE_") :]] = ServiceConfig(
                    json.loads(value)
                )

    def change_key(self):
        raise NotImplementedError("change_key is not supported in this keychain")

    def get_service(self, service_name):
        try:
            service = Service.objects.get(name=service_name)
            service_config = json.loads(service.json)
            return ServiceConfig(service_config)
        except Service.DoesNotExist:
            raise ServiceNotConfigured(service_name)

    def set_service(self, service_name, service_config):
        try:
            service = Service.objects.get(name=service_name)
            service.json = json.dumps(service_config.config)
        except Service.DoesNotExist:
            service = Service(
                name=service_name,
                json=json.dumps(service_config.config, cls=DjangoJSONEncoder),
            )
        service.save()

    def list_orgs(self):
        orgs = (
            Org.objects.filter(repo=self.build.repo)
            .order_by("name")
            .values_list("name", flat=True)
        )
        return orgs

    def get_default_org(self):
        raise NotImplementedError("get_default_org is not supported in this keychain")

    def set_default_org(self):
        raise NotImplementedError("set_default_org is not supported in this keychain")

    def get_org(self, org_name):
        org = Org.objects.get(repo=self.build.repo, name=org_name)
        org_config = json.loads(org.json)

        if org.scratch:
            config = ScratchOrgConfig(org_config, org.name, keychain=self)
        else:
            config = OrgConfig(org_config, org.name, keychain=self)

        # Attach the org model instance to the org config
        config.org = org
        config.org_instance = None

        # Initialize the scratch org instance
        if org.scratch:
            config = self._init_scratch_org(config)

        return config

    def _init_scratch_org(self, org_config):
        if not org_config.scratch:
            # Only run against scratch orgs
            return

        # Set up the logger to output to the build.log field
        init_logger(self.build)

        # Create the scratch org and get its info
        info = org_config.scratch_info

        org_json = json.dumps(org_config.config, cls=DjangoJSONEncoder)

        # Create a ScratchOrgInstance to store the org info
        instance = ScratchOrgInstance(
            org=org_config.org,
            build=self.build,
            sf_org_id=info["org_id"],
            username=info["username"],
            json=org_json,
            expiration_date=org_config.expires,
            org_note=self.build.org_note,
        )
        instance.save()
        org_config.org_instance = instance

        return org_config

    def set_org(self, org_config, global_org=True):
        org_json = json.dumps(org_config.config, cls=DjangoJSONEncoder)
        try:
            org = Org.objects.get(repo=self.build.repo, name=org_config.name)
            org.json = org_json
        except Org.DoesNotExist:
            org = Org(name=org_config.name, json=org_json, repo=self.build.repo)

        org.scratch = isinstance(org_config, ScratchOrgConfig)
        if not org.scratch:
            org.save()


class GitHubSettingsKeychain(object):
    """Limited keychain to supply GitHub credentials from Django settings"""

    def get_service(self, name):
        assert name == "github"
        return ServiceConfig(
            {"username": settings.GITHUB_USERNAME, "password": settings.GITHUB_PASSWORD}
        )
