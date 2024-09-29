# 配置
import json

class ConfigLoader:
    def __init__(self, config_file='config.json'):
        self.config_file = config_file
        self.env = None
        self.config = self.load_config_file()

    def load_config_file(self):
        with open(self.config_file, 'r') as f:
            return json.load(f)

    def set_environment(self, env=None):
        if env:
            self.env = env
        else:
            self.env = self.config.get('default_env', 'hospital_test')

    async def get_database(self):
        if not self.env:
            self.set_environment()
        env_config = self.config['environments'].get(self.env, {})
        return env_config.get('database', 'data/hospital_test.db')

    async def get_icon_path_dict(self):
        if not self.env:
            self.set_environment()
        env_config = self.config['environments'].get(self.env, {})
        return env_config.get('icon_path', {})

    async def get_icon_relative_path_dict(self):
        if not self.env:
            self.set_environment()
        env_config = self.config['environments'].get(self.env, {})
        return env_config.get('icon_relative_path', {})

class GlobalConfigManager:
    _config_loader_instance = None

    @staticmethod
    def get_config_loader(env=None):
        if GlobalConfigManager._config_loader_instance is None:
            GlobalConfigManager._config_loader_instance = ConfigLoader()
            GlobalConfigManager._config_loader_instance.set_environment(env)
        return GlobalConfigManager._config_loader_instance