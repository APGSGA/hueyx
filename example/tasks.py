from hueyx.consumers import hueyx


huey_queue1 = hueyx('queue1')

huey_queue2 = hueyx('queue2')


@huey_queue1.task()
def my_task1():
    print('my_task1 called')
    return 1

@huey_queue2.task()
def my_task2():
    print('my_task2 called')
    return 1
