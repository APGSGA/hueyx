import logging

from django.core.management.base import BaseCommand
from django.utils.module_loading import autodiscover_modules
from huey.consumer_options import ConsumerConfig

from hueyx.consumer import HueyxConsumer
from hueyx.queues import settings_reader

logger = logging.getLogger('huey.consumer')


class Command(BaseCommand):
    """
    Queue consumer. Example usage::
    To start the consumer (note you must export the settings module):
    django-admin.py run_hueyx
    """
    help = "Run a huey consumer on a specific pool"
    consumer_options = None

    def add_arguments(self, parser):
        parser.add_argument('queue_name', nargs=1, type=str, help='Select the queue to listen on.')

    def run_consumer(self, queue_name):
        multiple_scheduler_locking = self.consumer_options.pop('multiple_scheduler_locking', False)

        HUEY = settings_reader.configurations[queue_name].huey_instance

        config = ConsumerConfig(**self.consumer_options)
        config.validate()
        config.setup_logger()

        logger.info(f'Run huey on {queue_name}')
        consumer = HueyxConsumer(HUEY, multiple_scheduler_locking=multiple_scheduler_locking, **config.values)
        consumer.run()

    def handle(self, *args, **options):
        queue_name = options['queue_name'][0]
        self.consumer_options = settings_reader.configurations[queue_name].consumer_options

        autodiscover_modules("tasks")
        self.run_consumer(queue_name)
