from cumulusci.core.config import OrgConfig, ScratchOrgConfig, ServiceConfig
from cumulusci.core.exceptions import ServiceNotConfigured
from cumulusci.core.keychain import BaseProjectKeychain
from django.conf import settings
from django.utils import timezone

from metaci.cumulusci.logger import init_logger
from metaci.cumulusci.models import Org, ScratchOrgInstance, Service


class MetaCIProjectKeychain(BaseProjectKeychain):
    def __init__(self, project_config, key, build):
        self.build = build
        super(MetaCIProjectKeychain, self).__init__(project_config, key)

    def get_service(self, service_type, alias=None):
        if alias is not None:
            raise ValueError(
                f"CumulusCI tried to get {service_type} service named {alias} "
                "but MetaCI does not yet support named services."
            )
        try:
            service = Service.objects.get(name=service_type)
            return ServiceConfig(service.json)
        except Service.DoesNotExist:
            raise ServiceNotConfigured(service_type)

    def set_service(self, service_type, alias, service_config):
        raise NotImplementedError(
            f"CumulusCI tried to store {service_type} service named {alias} but MetaCI does not support this."
        )

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
        org_config = org.json

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

        # Create a ScratchOrgInstance to store the org info
        instance = ScratchOrgInstance(
            org=org_config.org,
            build=self.build,
            sf_org_id=info["org_id"],
            username=info["username"],
            json=org_config.config,
            expiration_date=timezone.make_aware(org_config.expires, timezone.utc),
            org_note=self.build.org_note,
        )
        instance.save()
        org_config.org_instance = instance

        return org_config

    def set_org(self, org_config, global_org=True):
        try:
            org = Org.objects.get(repo=self.build.repo, name=org_config.name)
            org.json = org_config.config
        except Org.DoesNotExist:
            org = Org(
                name=org_config.name, json=org_config.config, repo=self.build.repo
            )

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
