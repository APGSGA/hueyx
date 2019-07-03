import os

import prometheus_client
from prometheus_client import multiprocess
import logging

logger = logging.getLogger()


def env_var_set_check():
    dir = os.environ.get('prometheus_multiproc_dir', None)
    if not dir:
        print()
        print('Environment variable `prometheus_multiproc_dir` is not set. Exit exporter.')
        exit()


def clean_metrics_folder():
    folder = os.environ.get('prometheus_multiproc_dir', None)
    for the_file in os.listdir(folder):
        print('- Clean', folder, the_file)
        file_path = os.path.join(folder, the_file)
        try:
            if os.path.isfile(file_path):
                os.unlink(file_path)
        except Exception as e:
            logger.error(str(e))


def create_prometheus_app():
    registry = prometheus_client.CollectorRegistry()
    multiprocess.MultiProcessCollector(registry)
    application = prometheus_client.make_wsgi_app(registry)
    return application


env_var_set_check()
clean_metrics_folder()
application = create_prometheus_app()



