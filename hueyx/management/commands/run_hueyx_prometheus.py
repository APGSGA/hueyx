import logging
import os
import subprocess

from django.core.management.base import BaseCommand


logger = logging.getLogger('huey.consumer')


class Command(BaseCommand):

    help = "Runs the prometheus web server for hueyx"


    def add_arguments(self, parser):
        parser.add_argument('--port', nargs=1, type=int, default=9100, help='Select the port the metrics will be exposed')

    @property
    def prometheus_exporter_path(self):
        dir_path = os.path.dirname(os.path.realpath(__file__))
        hueyx_path = os.path.abspath(os.path.join(dir_path, '../..'))
        return os.path.join(hueyx_path, 'prometheus_exporter')

    @property
    def run_script_path(self):
        script_path = os.path.join(self.prometheus_exporter_path, 'run.sh')
        return script_path

    def write_uwsgi_ini(self, port):
        content = f"""
        [uwsgi]
        http-socket =:{port}
        wsgi-file = exporter.py
        """

        with open(self.prometheus_exporter_path + '/uwsgi.ini', 'w') as file:
            file.write(content)
            file.truncate()

    def handle(self, *args, **options):
        port = options['port']
        logger.info('Run web server on port', port)
        self.write_uwsgi_ini(port)
        subprocess.call(self.run_script_path, shell=True, cwd=self.prometheus_exporter_path)

