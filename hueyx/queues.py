from .redis_huey import RedisHuey
from functools import lru_cache

from .settings_reader import DjangoSettingsReader

settings_reader = DjangoSettingsReader()
settings_reader.interpret_settings()


def hueyx(queue_name: str) -> RedisHuey:
    return settings_reader.configurations[queue_name].huey_instance
