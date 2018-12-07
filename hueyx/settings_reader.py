from typing import Dict

from cached_property import cached_property
from django.conf import settings
from redis import ConnectionPool
from .redis_huey import RedisHuey


class HueyxException(Exception):
    pass


class SingleConfigReader:
    def __init__(self, name: str, config: Dict):
        self.name = name
        self.config = config

    @property
    def consumer_options(self):
        if 'consumer' not in self.config:
            raise HueyxException('No consumer configured.')
        return self.config['consumer']

    @cached_property
    def connection_pool(self) -> ConnectionPool:
        if 'connection' not in self.config:
            raise HueyxException('No connection configured.')

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
        config.pop('name', {})
        return config

    @cached_property
    def huey_instance(self):
        huey = RedisHuey(self.name, **self.huey_options, global_registry=False, connection_pool=self.connection_pool)

        return huey


class DjangoSettingsReader:
    def __init__(self):
        self.configurations: Dict[str, SingleConfigReader] = {}

    def interpret_settings(self):
        if not hasattr(settings, 'HUEYX'):
            raise HueyxException('No HUEYX config found in settings.py')

        for name, values in settings.HUEYX.items():
            reader = SingleConfigReader(name, values)
            self.configurations[name] = reader


