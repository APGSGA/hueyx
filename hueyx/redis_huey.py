from collections import namedtuple
from contextlib import contextmanager
from datetime import timedelta
from functools import wraps
from typing import List

from django.db import close_old_connections
from django.utils import timezone
from huey import Huey as HueyOriginal
from huey.api import Task
from huey.storage import RedisStorage, PriorityRedisStorage, RedisExpireStorage, PriorityRedisExpireStorage


class BaseHueyx(HueyOriginal):
    """
    Extends the Huey with new decorators which start a new transaction for every task.
    """

    DeadTask = namedtuple('DeadTask', ['id', 'name', 'settings'])
    HEARTBEAT_UPDATE_INTERVAL = 60  # min wait time in seconds to send another heartbeat to redis

    def db_task(self, *args, **kwargs):
        def decorator(fn):
            heartbeat_timeout = kwargs.pop('heartbeat_timeout', 0)
            if heartbeat_timeout:
                assert not kwargs.get('include_task',
                                      False), 'include_task and heartbeat_timeout keywords are not allowed together.'
                wrap = _wrap_heartbeat(close_db(fn, self), self, heartbeat_timeout)
                kwargs['context'] = True
            else:
                wrap = close_db(fn, self)
            task = self.task(*args, **kwargs)
            ret = task(wrap)
            ret.call_local = fn
            return ret

        return decorator

    def db_periodic_task(self, *args, **kwargs):
        def decorator(fn):
            return self.periodic_task(*args, **kwargs)(close_db(fn, self))

        return decorator

    @staticmethod
    def get_heartbeat_observation_key(task_id):
        return f'hb:{task_id}'

    @staticmethod
    def get_heartbeat_timestamp_key(task_id):
        return f'hbts:{task_id}'

    def get_dead_tasks(self) -> List[DeadTask]:
        dead_tasks = []
        observation_key_prefix = self.get_heartbeat_observation_key('')
        for result in self.storage.conn.hscan_iter(self.storage.result_key, match=observation_key_prefix + '*'):
            key = result[0].decode()
            task_id = key[len(observation_key_prefix):]
            name, task_settings, heartbeat_timeout = self.get(key, peek=True)
            timestamp = self.get(self.get_heartbeat_timestamp_key(task_id), peek=True)
            if not timestamp or timestamp + timedelta(seconds=heartbeat_timeout) <= timezone.now():
                dead_tasks.append(self.DeadTask(task_id, name, task_settings))
        return dead_tasks

    def restart_dead_tasks(self):
        for task in self.get_dead_tasks():
            task_type = self._registry.string_to_task(task.name)
            self.revoke_by_id(task.id)
            self.get(self.get_heartbeat_observation_key(task.id))
            task = task_type(**task.settings)
            self.enqueue(task)


class RedisHuey(BaseHueyx):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, storage_class=RedisStorage, **kwargs)


class PriorityRedisHuey(BaseHueyx):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, storage_class=PriorityRedisStorage, **kwargs)


class RedisExpireHuey(BaseHueyx):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, storage_class=RedisExpireStorage, **kwargs)


class PriorityRedisExpireHuey(BaseHueyx):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, storage_class=PriorityRedisExpireStorage, **kwargs)


def close_db(fn, huey: BaseHueyx):
    """Decorator to be used with tasks that may operate on the database."""

    @wraps(fn)
    def inner(*args, **kwargs):
        try:
            return fn(*args, **kwargs)
        finally:
            if not huey.immediate:
                close_old_connections()

    return inner


def _wrap_heartbeat(fn, huey: BaseHueyx, heartbeat_timeout: int):
    # noinspection PyProtectedMember
    @wraps(fn)
    def inner(*args, **kwargs):
        task: Task = kwargs.pop('task')
        heartbeat = Heartbeat(huey, task, heartbeat_timeout)
        heartbeat._start_heartbeat_observation()
        heartbeat._set_timestamp()
        result = None
        try:
            result = fn(*args, heartbeat=heartbeat, **kwargs)
        except HeartbeatTimeoutError:   # do not stop heartbeat observation -> task needs to be restarted
            return
        except RevokedError:    # stop heartbeat observation because task has been revoked
            pass
        except Exception as e:  # stop heartbeat observation and reraise exception
            heartbeat._stop_heartbeat_observation()
            raise e

        heartbeat._stop_heartbeat_observation()
        return result

    assert heartbeat_timeout >= 120, 'Minimal heartbeat_timeout is 120 seconds.'
    return inner


class RevokedError(Exception):
    pass


class HeartbeatTimeoutError(Exception):
    pass


class Heartbeat:

    CHECK_INTERVAL = timedelta(seconds=5)   # check timestamp just every 5 seconds -> otherwise redis can get heady load

    def __init__(self, huey: BaseHueyx, task: Task, heartbeat_timeout: int):
        self._huey = huey
        self.task = task
        self.heartbeat_timeout = heartbeat_timeout
        self.next_check = None

    @contextmanager
    def long_running_operation(self, delta: timedelta):
        self._set_timestamp(delta)
        yield
        self._set_timestamp()

    def __call__(self):
        if not self.next_check or self.next_check < timezone.now():
            self._check_timestamp()
            self.next_check = timezone.now() + self.CHECK_INTERVAL

    def _check_timestamp(self):
        """
        - Check if task has not been revoked -> RevokedError
        - Check if timestamp has not been expired -> HeartbeatTimeoutError
        Set new timestamp if checks are true
        """
        if self._huey.is_revoked(self.task):
            self._delete_timestamp()
            raise RevokedError()
        else:
            timestamp = self._get_timestamp()
            if not timestamp:
                raise HeartbeatTimeoutError()
            now = timezone.now()
            if timestamp + timedelta(seconds=self._huey.HEARTBEAT_UPDATE_INTERVAL) <= now:
                if timestamp + timedelta(seconds=self.heartbeat_timeout) <= now:
                    raise HeartbeatTimeoutError()
                self._set_timestamp()

    def _start_heartbeat_observation(self):
        """ Start heartbeat observation and save data to restart task if necessary. """
        args = self.task.args
        kwargs = self.task.kwargs
        if kwargs:
            kwargs.pop('task')
        task_settings = dict(on_complete=self.task.on_complete,
                             retries=self.task.retries, retry_delay=self.task.retry_delay, args=args, kwargs=kwargs)
        task_name = self.task.__module__ + '.' + self.task.name
        self._huey.put(self._huey.get_heartbeat_observation_key(self.task.id),
                       (task_name, task_settings, self.heartbeat_timeout))

    def _stop_heartbeat_observation(self):
        self._huey.get(self._huey.get_heartbeat_observation_key(self.task.id))

    def _set_timestamp(self, delta=timedelta()):
        self._huey.put(self._huey.get_heartbeat_timestamp_key(self.task.id), timezone.now() + delta)

    def _get_timestamp(self):
        return self._huey.get(self._huey.get_heartbeat_timestamp_key(self.task.id), peek=True)

    def _delete_timestamp(self):
        return self._huey.get(self._huey.get_heartbeat_timestamp_key(self.task.id), peek=False)
