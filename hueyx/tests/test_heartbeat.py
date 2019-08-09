from datetime import timedelta
from unittest.mock import MagicMock, patch

from django.test import TestCase
from django.utils import timezone
from huey.api import Task
from huey.constants import EmptyData

from hueyx.redis_huey import RedisHuey, Heartbeat, HeartbeatTimeoutError, RevokedError, _wrap_heartbeat


class RedisHueyMock(RedisHuey):

    def get_storage(self, *args, **kwargs):
        return MagicMock()

    def is_revoked(self, task, dt=None, peek=True):
        return False


class HeartbeatTest(TestCase):

    def example_func(self):
        return 0

    def setUp(self, *args):
        self.huey = RedisHueyMock()
        self.task = Task(retries=5, retry_delay=3)
        self.timeout = 120
        self.heartbeat = Heartbeat(self.huey, self.task, self.timeout)
        self.redis: MagicMock = self.huey.storage
        self.called = False
        self.call_cnt = 0

    def test_start_heartbeat_observation(self):
        self.heartbeat._start_heartbeat_observation()
        self.assertEqual(self.redis.method_calls[0][0], 'put_data')
        self.assertEqual(self.redis.method_calls[0][1][0], f'hb:{self.task.id}')

    def test_stop_heartbeat_observation(self):
        def pop_data(*args, **kwargs):
            self.assertEqual(args[0], f'hb:{self.task.id}')
            self.called = True
            return EmptyData

        self.redis.pop_data = pop_data
        self.heartbeat._stop_heartbeat_observation()
        self.assertTrue(self.called)

    def test_set_timestamp(self):
        self.heartbeat._set_timestamp()
        self.assertEqual(self.redis.method_calls[0][0], 'put_data')
        self.assertEqual(self.redis.method_calls[0][1][0], f'hbts:{self.task.id}')

    def test_get_timestamp(self):
        def peek_data(*args, **kwargs):
            self.assertEqual(args[0], f'hbts:{self.task.id}')
            self.called = True
            return EmptyData

        self.redis.peek_data = peek_data
        self.heartbeat._get_timestamp()
        self.assertTrue(self.called)

    def test_delete_timestamp(self):
        def pop_data(*args, **kwargs):
            self.assertEqual(args[0], f'hbts:{self.task.id}')
            self.called = True
            return EmptyData

        self.redis.pop_data = pop_data
        self.heartbeat._delete_timestamp()
        self.assertTrue(self.called)

    def test_heartbeat_no_new_timestamp(self):
        def get_timestamp():
            self.called = True
            return timezone.now()

        self.heartbeat._get_timestamp = get_timestamp
        self.heartbeat()
        self.assertTrue(self.called)

    def test_heartbeat_new_timestamp(self):
        def get_timestamp():
            return timezone.now() - timedelta(seconds=self.huey.heartbeat_manager.HEARTBEAT_UPDATE_INTERVAL)

        def set_timestamp():
            self.called = True

        self.heartbeat._get_timestamp = get_timestamp
        self.heartbeat._set_timestamp = set_timestamp
        self.heartbeat()
        self.assertTrue(self.called)

    def test_heartbeat_no_timestamp(self):
        def get_timestamp():
            return None

        def set_timestamp():
            self.called = True

        self.heartbeat._get_timestamp = get_timestamp
        self.heartbeat._set_timestamp = set_timestamp
        with self.assertRaises(HeartbeatTimeoutError):
            self.heartbeat()
        self.assertFalse(self.called)

    def test_heartbeat_expired_timestamp(self):
        def get_timestamp():
            return timezone.now() - timedelta(seconds=self.timeout)

        def set_timestamp():
            self.called = True

        self.heartbeat._get_timestamp = get_timestamp
        self.heartbeat._set_timestamp = set_timestamp
        with self.assertRaises(HeartbeatTimeoutError):
            self.heartbeat()
        self.assertFalse(self.called)

    def test_heartbeat_revoked(self):
        def delete_timestamp():
            self.called = True

        self.huey.is_revoked = MagicMock(return_value=True)
        self.heartbeat._delete_timestamp = delete_timestamp
        with self.assertRaises(RevokedError):
            self.heartbeat()
        self.assertTrue(self.called)

    def test_caching(self):
        def get_timestamp():
            self.call_cnt += 1
            return timezone.now() - timedelta(seconds=self.huey.heartbeat_manager.HEARTBEAT_UPDATE_INTERVAL)

        self.heartbeat._get_timestamp = get_timestamp
        self.heartbeat()
        self.heartbeat()
        self.assertEqual(self.call_cnt, 1)

    def test_no_caching(self):
        def get_timestamp():
            self.call_cnt += 1
            return timezone.now() - timedelta(seconds=self.huey.heartbeat_manager.HEARTBEAT_UPDATE_INTERVAL)

        self.heartbeat._get_timestamp = get_timestamp
        self.heartbeat.CHECK_INTERVAL = timedelta()
        self.heartbeat()
        self.heartbeat()
        self.assertEqual(self.call_cnt, 2)


class HeartbeatMock(MagicMock):

    def _start_heartbeat_observation(self):
        self.calls = ['start']

    def _set_timestamp(self):
        self.calls.append('timestamp')

    def _stop_heartbeat_observation(self):
        self.calls.append('stop')


@patch('hueyx.redis_huey.Heartbeat', new_callable=HeartbeatMock)
class HeartbeatWrapperTest(TestCase):
    def setUp(self):
        self.huey = RedisHueyMock()
        self.task = Task(retries=5, retry_delay=3)
        self.timeout = 120
        self.heartbeat = None

    def test_task_execution(self, *args):
        def task(heartbeat):
            self.heartbeat = heartbeat
            return 'finish'

        result = _wrap_heartbeat(task, self.huey, self.timeout)(task=self.task)
        self.assertEqual(result, 'finish')
        self.assertEqual(self.heartbeat.calls, ['start', 'timestamp', 'stop'])

    def test_timeout(self, *args):
        def task(heartbeat):
            self.heartbeat = heartbeat
            raise HeartbeatTimeoutError()

        result = _wrap_heartbeat(task, self.huey, self.timeout)(task=self.task)
        self.assertEqual(result, None)
        self.assertEqual(self.heartbeat.calls, ['start', 'timestamp'])

    def test_revoke(self, *args):
        def task(heartbeat):
            self.heartbeat = heartbeat
            raise RevokedError()

        result = _wrap_heartbeat(task, self.huey, self.timeout)(task=self.task)
        self.assertEqual(result, None)
        self.assertEqual(self.heartbeat.calls, ['start', 'timestamp', 'stop'])

    def test_exception(self, *args):
        def task(heartbeat):
            self.heartbeat = heartbeat
            raise Exception()

        with self.assertRaises(Exception):
            _wrap_heartbeat(task, self.huey, self.timeout)(task=self.task)
        self.assertEqual(self.heartbeat.calls, ['start', 'timestamp', 'stop'])


class RedisMock(MagicMock):

    @property
    def conn(self, *args, **kwargs):
        return self

    # noinspection PyMethodMayBeStatic
    def hscan_iter(self, *args, **kwargs):
        return [[b'hb:task-id']]


class RedisHueyTest(TestCase):

    # @patch('huey.storage.RedisStorage', new_callable=RedisMock)
    def setUp(self, *args):
        self.huey = RedisHuey()
        self.huey.storage = RedisMock()
        self.called = False

    def test_no_dead_tasks(self):
        def get(key, *args, peek, **kwargs):
            assert peek
            self.called = True
            if key.startswith('hb:'):
                return 'name', 'settings', 60
            return timezone.now()

        self.huey.get = get
        tasks = self.huey.heartbeat_manager.get_dead_tasks()
        self.assertEqual(len(tasks), 0)
        self.assertTrue(self.called)

    def test_dead_tasks_no_timestamp(self):
        def get(key, *args, peek, **kwargs):
            assert peek
            self.called = True
            if key.startswith('hb:'):
                return 'name', 'settings', 60

        self.huey.get = get
        tasks = self.huey.heartbeat_manager.get_dead_tasks()
        self.assertEqual(len(tasks), 1)
        self.assertEqual(tasks[0], self.huey.heartbeat_manager.DeadTask('task-id', 'name', 'settings'))
        self.assertTrue(self.called)

    def test_dead_tasks_timestamp_expired(self):
        def get(key, *args, peek, **kwargs):
            assert peek
            self.called = True
            if key.startswith('hb:'):
                return 'name', 'settings', 60
            return timezone.now() - timedelta(seconds=60)

        self.huey.get = get
        tasks = self.huey.heartbeat_manager.get_dead_tasks()
        self.assertEqual(len(tasks), 1)
        self.assertEqual(tasks[0], self.huey.heartbeat_manager.DeadTask('task-id', 'name', 'settings'))
        self.assertTrue(self.called)
