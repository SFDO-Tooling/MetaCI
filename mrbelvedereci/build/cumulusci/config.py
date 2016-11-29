from cumulusci.core.config import YamlGlobalConfig
from cumulusci.core.config import YamlProjectConfig

class MrbelvedereProjectConfig(YamlProjectConfig):
    def __init__(self, global_config_obj, build_flow):
        super(MrbelvedereProjectConfig, self).__init__(global_config_obj)
        self.build_flow = build_flow

    @property
    def config_project_local_path(self):
        """ mrbelvedere never uses the local path """
        return
    @property
    def repo_root(self):
        return build_flow.build_dir
    @property
    def repo_name(self):
        return build_flow.build.repo.name
    @property
    def repo_url(self):
        return build_flow.build.repo.url
    @property
    def repo_owner(self):
        return build_flow.build.repo.url.split('/')[-2]
    @property
    def repo_branch(self):
        return build_flow.build.branch.name
    @property
    def repo_commit(self):
        return build_flow.build.commit

class MrbelvedereGlobalConfig(YamlGlobalConfig):
    project_config_class = MrbelvedereProjectConfig

    def get_project_config(self, build_flow):
        return self.project_config_class(self, build_flow)
