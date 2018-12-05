from hueyx.consumers import hueyx

HUEY_Q1 = hueyx('queue1')
HUEY_Q2 = hueyx('queue2')


@HUEY_Q1.task()
def my_task1():
    print('my_task1 called')
    return 1


@HUEY_Q2.task()
def my_task2():
    print('my_task2 called')
    return 1
