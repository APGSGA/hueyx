import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "huey_worker.settings")
django.setup()


from example.tasks import my_long_running_task1

my_long_running_task1()