from collections import namedtuple
from contextlib import contextmanager
from datetime import timedelta
from functools import wraps
from typing import List

from django.db import close_old_connections
from django.utils import timezone
from huey import RedisHuey as RedisHueyOriginal
from huey.api import QueueTask, TaskWrapper

EVENT_ENQUEUED = 'enqueued'


class RedisHuey(RedisHueyOriginal):
    def __init__(self, *args, **kwargs):
        self._fire_enqueued_event = kwargs.pop('fire_enqueued_events', False)
        super().__init__(*args, **kwargs)

    """
    Extends the RedisHuey with new decorators which start a new transaction for every task.
    """

    def db_task(self, *args, **kwargs):
        def decorator(fn):
            timeout = kwargs.pop('timeout', 0)
            if timeout:
                wrap = _wrap_heartbeat(close_db(fn, self), self, timeout, kwargs)
                kwargs['include_task'] = True
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

    def enqueue(self, task):
        """
        Send an additional event when a task is enqueued. This is done for prometheus.
        :param task:
        :return:
        """
        super(RedisHuey, self).enqueue(task)
        if not self.always_eager and self._fire_enqueued_event:
            self.emit_task(EVENT_ENQUEUED, task)

    DeadTask = namedtuple('DeadTask', ['id', 'name', 'args', 'kwargs'])
    HEARTBEAT_UPDATE_INTERVAL = 60  # min wait time in seconds to send another heartbeat to redis

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
            task_name, timeout, args, kwargs = self.get(key, peek=True)
            timestamp = self.get(self.get_heartbeat_timestamp_key(task_id))
            if not timestamp or timestamp + timedelta(seconds=timeout) <= timezone.now():
                dead_tasks.append(self.DeadTask(task_id, task_name, args, kwargs))
        return dead_tasks

    restartable_tasks = set()

    def register_for_restart(self, task_wrapper: TaskWrapper):
        if task_wrapper.task_class.__name__ not in [tw.task_class.__name__ for tw in self.restartable_tasks]:
            self.restartable_tasks.add(task_wrapper)


def close_db(fn, huey: RedisHuey):
    """Decorator to be used with tasks that may operate on the database."""

    @wraps(fn)
    def inner(*args, **kwargs):
        try:
            return fn(*args, **kwargs)
        finally:
            if not huey.always_eager:
                close_old_connections()

    return inner


def _wrap_heartbeat(fn, huey: RedisHuey, timeout: int, kwargs):
    # noinspection PyProtectedMember
    @wraps(fn)
    def inner(*args, **kwargs):
        task: QueueTask = kwargs.pop('task')
        heartbeat = Heartbeat(huey, task, timeout, args, kwargs)
        heartbeat._start_heartbeat_observation()
        heartbeat._set_timestamp()
        try:
            result = fn(*args, heartbeat=heartbeat, **kwargs)
        finally:
            heartbeat._stop_heartbeat_observation()
        return result

    assert timeout >= 120, 'Minimal timeout is 120 seconds.'
    assert not kwargs.get('include_task', False), 'include_task and timeout keywords are not allowed together.'
    return inner


class Heartbeat:

    def __init__(self, huey: RedisHuey, task: QueueTask, timeout: int, args, kwargs):
        self._huey = huey
        self.task = task
        self.timeout = timeout
        self.args = args
        self.kwargs = kwargs

    @contextmanager
    def long_running_operation(self, delta: timedelta):
        self._set_timestamp(delta)
        yield
        self._set_timestamp()

    def __call__(self):
        if self._huey.is_revoked(self.task):
            self._delete_timestamp()
            return False
        else:
            timestamp = self._get_timestamp()
            if not timestamp:
                return
            now = timezone.now()
            if timestamp + timedelta(seconds=self._huey.HEARTBEAT_UPDATE_INTERVAL) <= now:
                if timestamp + timedelta(seconds=self.timeout) <= now:
                    return False
                self._set_timestamp()
        return True

    def _start_heartbeat_observation(self):
        self._huey.put(self._huey.get_heartbeat_observation_key(self.task.task_id),
                       (self.task.name, self.timeout, self.args, self.kwargs))

    def _stop_heartbeat_observation(self):
        self._huey.get(self._huey.get_heartbeat_observation_key(self.task.task_id))

    def _set_timestamp(self, delta=timedelta()):
        self._huey.put(self._huey.get_heartbeat_timestamp_key(self.task.task_id), timezone.now() + delta)

    def _get_timestamp(self):
        return self._huey.get(self._huey.get_heartbeat_timestamp_key(self.task.task_id), peek=True)

    def _delete_timestamp(self):
        return self._huey.get(self._huey.get_heartbeat_timestamp_key(self.task.task_id), peek=False)
