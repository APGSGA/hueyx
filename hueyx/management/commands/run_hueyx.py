import imp
import logging
import os

from django.apps import apps as django_apps
from django.core.management.base import BaseCommand

from huey.consumer_options import ConsumerConfig
from hueyx.consumer import HueyxConsumer
from hueyx.queues import settings_reader

try:
    from prometheus_client import multiprocess
    from prometheus_client import generate_latest, CollectorRegistry

    PROMETHEUS_AVAILABLE = True
except Exception as e:
    PROMETHEUS_AVAILABLE = False


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

        multiple_scheduler_locking = self.consumer_options.pop('multiple_scheduler_locking', False)

        HUEY = settings_reader.configurations[queue_name].huey_instance

        config = ConsumerConfig(**self.consumer_options)
        config.validate()
        config.setup_logger()

        logger.info(f'Run huey on {queue_name}')
        consumer = HueyxConsumer(HUEY, multiple_scheduler_locking=multiple_scheduler_locking, **config.values)
        consumer.run()

    def write_prometheus_metric_to_folder(self):
        if os.environ.get('') is None:
            logger.info('"prometheus_multiproc_dir" not provided. Start prometheus webserver only.')
            return
        registry = CollectorRegistry()
        multiprocess.MultiProcessCollector(registry)
        generate_latest(registry)

    def handle(self, *args, **options):
        queue_name = options['queue_name'][0]
        self.consumer_options = settings_reader.configurations[queue_name].consumer_options

        prometheus_enabled = self.consumer_options.pop('prometheus_metrics', False)
        if PROMETHEUS_AVAILABLE and prometheus_enabled:
            logger.info('Prometheus is available and activated. Start writing to registry')
            self.write_prometheus_metric_to_folder()
        else:
            logger.info('Prometheus not available.')

        self.autodiscover()
        self.run_consumer(queue_name)

