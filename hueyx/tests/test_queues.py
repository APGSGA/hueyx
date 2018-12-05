from django.test import TestCase


HUEYX = {
    'queue1': {
        'connection': {
            'host': 'localhost',
            'port': 6379,
            'db': 98
        },
        'consumer': {
            'workers': 4,
            'worker_type': 'process',
        }
    },
    'queue2': {
        'connection': {
            'host': 'localhost',
            'port': 6379,
            'db': 99
        },
        'consumer': {
            'workers': 4,
            'worker_type': 'process',
        }
    },
}


class QueuesTest(TestCase):
    def test_settings_interpretation(self):
        with self.settings(HUEYX=HUEYX):
            from hueyx.queues import hueyx

            self.assertIsNotNone(hueyx('queue1'))
            self.assertIsNotNone(hueyx('queue2'))

    def test_huey_instance_caching(self):
        with self.settings(HUEYX=HUEYX):
            from hueyx.queues import hueyx

            self.assertEqual(hueyx('queue1'), hueyx('queue1'))

