from .redis_huey import RedisHuey
from functools import lru_cache

from .settings_reader import DjangoSettingsReader

settings_reader = DjangoSettingsReader()
settings_reader.interpret_settings()


def hueyx(queue_name) -> RedisHuey:
    return _huey(queue_name)


@lru_cache(maxsize=100)  # Cache the huey instances so they are not created with every call.
def _huey(queue_name) -> RedisHuey:
    return settings_reader.configurations[queue_name].huey_instance




