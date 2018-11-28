from cumulusci.core.config import BaseGlobalConfig
from cumulusci.core.config import BaseProjectConfig


class MetaCIProjectConfig(BaseProjectConfig):

    def __init__(self, global_config_obj, build, *args, **kwargs):
        self.build = build

        if 'additional_yaml' not in kwargs:
            kwargs['additional_yaml'] = build.plan.yaml_config

        super(MetaCIProjectConfig, self).__init__(global_config_obj, *args, **kwargs)

    @property
    def config_project_local_path(self):
        """ MetaCI never uses the local path """
        return

    @property
    def repo_root(self):
        return self.build.build_dir

    @property
    def repo_name(self):
        return self.build.repo.name

    @property
    def repo_url(self):
        return self.build.repo.url

    @property
    def repo_owner(self):
        return self.build.repo.url.split('/')[-2]

    @property
    def repo_branch(self):
        return self.build.branch.name

    @property
    def repo_commit(self):
        return self.build.commit


class MetaCIGlobalConfig(BaseGlobalConfig):
    project_config_class = MetaCIProjectConfig

    @property
    def config_global_local_path(self):
        """ MetaCI never uses the local path """
        return

    def get_project_config(self, build):
        return self.project_config_class(self, build)
