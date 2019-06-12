import os
from typing import Dict

from cached_property import cached_property
from django.conf import settings
from redis import ConnectionPool

from .redis_huey import RedisHuey

try:
    from prometheus_client import multiprocess, Counter
    from prometheus_client import generate_latest, CollectorRegistry
    PROMETHEUS_AVAILABLE = True
except Exception as e:
    PROMETHEUS_AVAILABLE = False


if PROMETHEUS_AVAILABLE:
    EVENT_COUNTER = Counter('hueyx_task_events',
                            'Counts the amount of signals by huey.',
                            ['queue', 'task', 'signal'])


class HueyxException(Exception):
    pass


class SingleConfigReader:
    def __init__(self, name: str, config: Dict):
        self.name = name
        self.config = config
        self._is_prometheus_initialized = False

    @property
    def consumer_options(self):
        if 'prometheus_metrics_enabled' in self.config:
            self.config.pop('prometheus_metrics_enabled')
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
        if PROMETHEUS_AVAILABLE:
            self._connect_signals_to_prometheus(huey)
        return huey

    def _initialize_prometheus(self):
        if not self._is_prometheus_initialized:
            if os.environ.get('') is None:
                print('"prometheus_multiproc_dir" not provided. Start prometheus webserver only.')
                return
            registry = CollectorRegistry()
            multiprocess.MultiProcessCollector(registry)
            generate_latest(registry)
            self._is_prometheus_initialized = True


    def _connect_signals_to_prometheus(self, huey: RedisHuey):
        huey._signal.connect(self._on_signal_received)

    def _on_signal_received(self, signal, task, exc=None):
        queue = self.huey_instance.name
        print('signal received:', signal)
        EVENT_COUNTER.labels(queue=queue, task=task.name, signal=signal).inc()


class DjangoSettingsReader:
    def __init__(self):
        self.configurations: Dict[str, SingleConfigReader] = {}

    def interpret_settings(self):
        if not hasattr(settings, 'HUEYX'):
            raise HueyxException('No HUEYX config found in settings.py')

        for name, values in settings.HUEYX.items():
            reader = SingleConfigReader(name, values)
            self.configurations[name] = reader
