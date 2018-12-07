# hueyx

[![PyPI version](https://badge.fury.io/py/hueyx.svg)](https://badge.fury.io/py/hueyx)

A django extension to run huey with multiple queues.
Multiple queues allow tasks not to block each other and to scale independently.
Only the redis storage is supported.

### Usage

Install it with
```bash
pip install hueyx
```

Add hueyx in your installed apps.

```python
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'hueyx',
]
```



##### settings.py

Compared to djhuey, hueyx allows several queues to be defined in the settings.py. 

```python
HUEYX = {
    'queue_name1': {
        'result_store': True,
        'store_none': False,
        'connection': {'host': 'localhost', 'port': 6379, db: 5},
            'consumer': {
                'workers': 4,
                'worker_type': 'process',
        }
    },
    'queue_name2': {
        'connection': {
            'connection_pool': ConnectionPool(host='localhost', port=6379, db=1)
        },
            'consumer': {
                'workers': 1,
                'worker_type': 'process',
        }
    },
}
```

The settings are almost the same as in [djhuey](https://huey.readthedocs.io/en/latest/contrib.html#setting-things-up)
Exceptions:
- You can only configure redis as storage engine.
- The option `multiple_scheduler_locking` has been added. See below.


##### tasks.py

```python
from hueyx.queues import hueyx

"""
Define which queue you want to use.
They are predefined in settings.py.
"""
HUEY_Q1 = hueyx('queue_name1')
HUEY_Q2 = hueyx('queue_name2')


@HUEY_Q1.task()
def my_task1():
    print('my_task1 called')
    
@HUEY_Q1.db_task()
def my_db_task1():
    print('my_db_task1 called')
    
@HUEY_Q2.task()
def my_task2():
    print('my_task2 called')

@HUEY_Q2.periodic_task(crontab(minute='0', hour='3'))
def my_periodic_task2():
    print('my_periodic_task2 called')
    return 1
```

##### Push task to queue
```python
from example.tasks import my_task1, my_db_task1, my_task2


my_task1()  # Task for queue_name1
my_db_task1()  # Task for queue_name1
my_task2()  # Task for queue_name2
```

##### Run consumer
Consumers are started with the queue_name.
```bash
./manage.py run_hueyx queue_name1
```

### Additional settings
`multiple_scheduler_locking` has been added to support multiple huey schedulers.
If you run huey in a cloud environment, you will end up running multiple huey instances which each will
schedule the periodic task.
`multiple_scheduler_locking` prevents periodic tasks to be scheduled multiple times.

```python
HUEYX = {
    'queue_name2': {
        'connection': {
            'connection_pool': ConnectionPool(host='localhost', port=6379, db=1)
        },
            'consumer': {
                'multiple_scheduler_locking': True,
                'workers': 1,
                'worker_type': 'process',
        }
    },
}
```

### Collaborators

- [Update hueyx on PyPi](./update_version.md)