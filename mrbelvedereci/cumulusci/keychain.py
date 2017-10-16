import json
import os
from cumulusci.core.keychain import BaseProjectKeychain
from cumulusci.core.config import OrgConfig
from cumulusci.core.config import ScratchOrgConfig
from cumulusci.core.config import ServiceConfig
from cumulusci.core.exceptions import ServiceNotConfigured
from django.conf import settings
from mrbelvedereci.cumulusci.logger import init_logger
from mrbelvedereci.cumulusci.models import Org
from mrbelvedereci.cumulusci.models import ScratchOrgInstance
from mrbelvedereci.cumulusci.models import Service
from mrbelvedereci.cumulusci.utils import get_connected_app


class MrbelvedereProjectKeychain(BaseProjectKeychain):

    def __init__(self, project_config, key, build):
        self.build = build
        super(MrbelvedereProjectKeychain, self).__init__(project_config, key)

    def _load_keychain_services(self):
        for key, value in settings.__dict__['_wrapped'].__dict__.items():
            if key.startswith('CUMULUSCI_SERVICE_'):
                print '%%% DEBUG %%%: {}'.format(key[len('CUMULUSCI_SERVICE_'):])
                self.services[key[len('CUMULUSCI_SERVICE_'):]] = ServiceConfig(json.loads(value))

    def change_key(self):
        raise NotImplementedError('change_key is not supported in this keychain')

    def set_connected_app(self):
        raise NotImplementedError('set_connected_app is not supported in this keychain')

    def get_connected_app(self):
        return get_connected_app()

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
                json=json.dumps(service_config.config),
            )
        service.save()

    def list_orgs(self):
        raise NotImplementedError('list_orgs is not supported in this keychain')

    def get_default_org(self):
        raise NotImplementedError('get_default_org is not supported in this keychain')

    def set_default_org(self):
        raise NotImplementedError('set_default_org is not supported in this keychain')

    def get_org(self, org_name):
        org = Org.objects.get(repo=self.build.repo, name=org_name)
        org_config = json.loads(org.json)

        if org.scratch:
            config = ScratchOrgConfig(org_config)
        else:
            config = OrgConfig(org_config)

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

        # Get the contents of the org's json file from Salesforce DX
        json_path = os.path.join(os.path.expanduser('~'), '.sfdx', info['username'] + '.json')
        if not os.path.isfile(json_path):
            json_path = os.path.join(os.path.expanduser('~'), '.local', '.sfdx', info['username'] + '.json')
        with open(json_path, 'r') as json_file:
            dx_json = json_file.read()

        org_json = json.dumps(org_config.config)

        # Create a ScratchOrgInstance to store the org info
        instance = ScratchOrgInstance(
            org=org_config.org,
            build=self.build,
            sf_org_id=info['org_id'],
            username=info['username'],
            json_dx=dx_json,
            json=org_json,
        )
        instance.save()
        org_config.org_instance = instance

        return org_config

    def set_org(self, org_name, org_config):
        try:
            org = Org.objects.get(repo=self.build.repo, name=org_name)
            org.json = json.dumps(org_config.config)
        except Org.DoesNotExist:
            org = Org(
                name=org_name,
                json=json.dumps(org_config.config),
                repo=self.build.repo,
            )

        org.scratch = isinstance(org_config, ScratchOrgConfig)
        org.save()
