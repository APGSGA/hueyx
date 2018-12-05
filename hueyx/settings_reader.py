from typing import Dict, List

from django.conf import settings
from redis import ConnectionPool
from huey import RedisHuey


class SingleConfigReader:
    def __init__(self, name: str, config: Dict):
        self.name = name
        self.config = config

    @property
    def consumer_options(self):
        if 'consumer' in self.config:
            return self.config['consumer']

        return {}

    @property
    def connection_pool(self) -> ConnectionPool:
        if 'connection' not in self.config:
            return None

        connection = self.config['connection']
        if 'connection_pool' in connection:
            return connection['connection_pool']
        else:
            return ConnectionPool(**connection)

    @property
    def huey_options(self):
        config = self.config.copy()
        config.pop('connection', {})
        config.pop('consumer', {})
        config.pop('backend_class', {})
        return config

    @property
    def huey_instance(self):
        return RedisHuey(self.name, **self.huey_options, connection_pool=self.connection_pool)


class DjangoSettingsReader:
    def __init__(self):
        self.configurations: Dict[str, SingleConfigReader] = {}

    def interpret_settings(self):
        if not hasattr(settings, 'HUEYX'):
            return

        for name, values in settings.HUEYX.items():
            reader = SingleConfigReader(name, values)
            self.configurations[name] = reader


