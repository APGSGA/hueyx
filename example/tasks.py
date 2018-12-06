import datetime

from huey import crontab

from hueyx.queues import hueyx

HUEY_Q1 = hueyx('queue1')
HUEY_Q2 = hueyx('queue2')


@HUEY_Q1.task()
def my_task1():
    print('my_task1 called')
    return 1


@HUEY_Q1.db_task()
def my_db_task1():
    print('my_db_task1 called')
    return 1


@HUEY_Q2.task()
def my_task2():
    print('my_task2 called')
    return 1


@HUEY_Q2.periodic_task(crontab(minute='*/1'))
def my_periodic_task2():
    print('my_periodic_task2 called', datetime.datetime.now())
    return 1
