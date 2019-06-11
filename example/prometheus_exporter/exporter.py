import os

import prometheus_client
from prometheus_client import multiprocess
import atexit
import logging

logger = logging.getLogger()


def register_shutdown():
    def on_shutdown():
        pid = os.getpid()
        logger.info('shutdown', pid)
        multiprocess.mark_process_dead(pid)


    atexit.register(on_shutdown)


def clean_metrics_folder():
    dir = os.environ.get('prometheus_multiproc_dir', None)
    folder = dir
    for the_file in os.listdir(folder):
        file_path = os.path.join(folder, the_file)
        try:
            if os.path.isfile(file_path):
                os.unlink(file_path)
            # elif os.path.isdir(file_path): shutil.rmtree(file_path)
        except Exception as e:
            logger.error(str(e))


def create_prometheus_app():
    registry = prometheus_client.CollectorRegistry()
    multiprocess.MultiProcessCollector(registry)
    application = prometheus_client.make_wsgi_app(registry)
    return application


clean_metrics_folder()
# register_shutdown()
application = create_prometheus_app()



