import os
import django


os.environ.setdefault("DJANGO_SETTINGS_MODULE", "huey_worker.settings")
django.setup()


from example.tasks import my_task1, my_task2


my_task1()  # Task for queue1
my_task2()  # Task for queue2
