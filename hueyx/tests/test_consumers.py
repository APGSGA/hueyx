from django.test import TestCase


HUEY = {
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


class ConsumerTest(TestCase):
    def test_settings_interpretation(self):
        with self.settings(HUEY=HUEY):
            from hueyx.consumers import hueyx

            self.assertIsNotNone(hueyx('queue1'))
            self.assertIsNotNone(hueyx('queue2'))

    def test_huey_instance_caching(self):
        with self.settings(HUEY=HUEY):
            from hueyx.consumers import hueyx

            self.assertEqual(hueyx('queue1'), hueyx('queue1'))

