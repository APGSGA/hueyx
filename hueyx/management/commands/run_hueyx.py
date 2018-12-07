import imp
import logging

from django.apps import apps as django_apps
from django.core.management.base import BaseCommand
from huey.consumer import Consumer
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

    def add_arguments(self, parser):
        parser.add_argument('queue_name', nargs=1, type=str, help='Select the queue to listen on.')

    def autodiscover(self):
        """Use Django app registry to pull out potential apps with tasks.py module."""
        module_name = 'tasks'
        for config in django_apps.get_app_configs():
            app_path = config.module.__path__
            try:
                fp, path, description = imp.find_module(module_name, app_path)
            except ImportError:
                continue
            else:
                import_path = '%s.%s' % (config.name, module_name)
                try:
                    imp.load_module(import_path, fp, path, description)
                except ImportError:
                    logger.exception('Found "%s" but error raised attempting '
                                     'to load module.', import_path)

    def run_consumer(self, queue_name):
        consumer_options = settings_reader.configurations[queue_name].consumer_options
        multiple_scheduler_locking = self.get_multiple_scheduler_locking_param(consumer_options)

        HUEY = settings_reader.configurations[queue_name].huey_instance
        config = ConsumerConfig(**consumer_options)
        config.validate()
        config.setup_logger()

        logger.info(f'Run huey on {queue_name}')
        consumer = HueyxConsumer(HUEY, multiple_scheduler_locking=multiple_scheduler_locking, **config.values)
        consumer.run()

    def get_multiple_scheduler_locking_param(self, consumer_options) -> bool:
        if 'multiple_scheduler_locking' not in consumer_options:
            return False
        else:
            return consumer_options['multiple_scheduler_locking']

    def handle(self, *args, **options):
        queue_name = options['queue_name'][0]
        self.autodiscover()

        self.run_consumer(queue_name)

