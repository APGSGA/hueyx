from typing import Dict, List

from django.test import TestCase
from redis import ConnectionPool

from worker.settings_reader import SingleConfigReader


class SingleConfigReaderTest(TestCase):
    def test_extract_consumer_options(self):
        config = {
            'consumer': {
                'workers': 4,
                'worker_type': 'process',
            }
        }
        reader = SingleConfigReader('queue1', config)
        self.assertEqual(reader.consumer_options, {
                'workers': 4,
                'worker_type': 'process',
            }
                         )

    def test_extract_connection(self):
        config = {
            'connection': {
                'host': 'localhost',
                'port': 6379,
                'db': 99
            }
        }
        reader = SingleConfigReader('queue1', config)
        pool = reader.connection_pool
        self.assertIsNotNone(pool)
        self.assertEqual(pool.connection_kwargs['db'], 99)

    def test_extract_connection_pool(self):
        config = {
            'connection': {
                'connection_pool': ConnectionPool(host='localhost', port=6379, db=99)
            }
        }
        reader = SingleConfigReader('queue1', config)
        pool = reader.connection_pool
        self.assertIsNotNone(pool)
        self.assertEqual(pool.connection_kwargs['db'], 99)

    def test_extract_none_connection(self):
        reader = SingleConfigReader('queue1', {})
        pool = reader.connection_pool
        self.assertIsNone(pool)

    def test_extract_huey_configuration(self):
        config = {
            'result_store': True,
            'always_eager': False,
            'backend_class': ' huey.RedisHuey',
            'connection': {
                'connection_pool': ConnectionPool(host='localhost', port=6379, db=99)
            }
        }
        reader = SingleConfigReader('queue1', config)
        huey_options = reader.huey_options
        self.assertEqual(huey_options, {
            'result_store': True,
            'always_eager': False
        })

    def test_get_huey_instance(self):
        config = {
            'result_store': False,
            'always_eager': False,
            'backend_class': ' huey.RedisHuey',
            'connection': {
                'connection_pool': ConnectionPool(host='localhost', port=6379, db=99)
            }
        }
        reader = SingleConfigReader('queue1', config)
        huey = reader.huey_instance
        self.assertIsNotNone(huey)
        self.assertEqual(huey.result_store, False)
        self.assertEqual(huey.storage.pool.connection_kwargs['db'], 99)
        self.assertEqual(huey.name, 'queue1')
