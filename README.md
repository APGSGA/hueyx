# hueyx

A django extension to run huey with multiple queues.
Multiple queue allow tasks not to block each other and to scale tasks independently.
Only the redis storage is supported by hueyx.

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

Compared to djhuey, hueyx allows several queue's to be defined in the settings.py. 

##### settings.py
```python
HUEY = {
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

The settings are the same as in [djhuey](https://huey.readthedocs.io/en/latest/contrib.html#setting-things-up)
except that you can only configure redis as storage engine.


##### tasks.py

```python
from hueyx.consumers import hueyx

"""
Define which queue you want to use.
"""
HUEY_Q1 = hueyx('queue_name1')
HUEY_Q2 = hueyx('queue_name2')


@HUEY_Q1.task()
def my_task1():
    print('my_task1 called')
    
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
from example.tasks import my_task1, my_task2


my_task1()  # Task for queue_name1
my_task2()  # Task for queue_name2
```

##### Run consumer
Consumers are started with the queue_name.
```bash
./manage.py run_hueyx queue_name1
```


### Collaborator

- [Update hueyx on PyPi](./update_version.md)