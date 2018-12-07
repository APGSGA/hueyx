# hueyx

[![PyPI version](https://badge.fury.io/py/hueyx.svg)](https://badge.fury.io/py/hueyx)

A django extension to run huey with multiple queues.
Multiple queues allow tasks to not block each other and to scale independently.
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
        'result_store': True,  # Store return values of tasks.
        'events': True,  # Consumer emits events allowing real-time monitoring.
        'store_none': False,  # If a task returns None, do not save to results.
        'always_eager': settings.DEBUG,  # If DEBUG=True, run synchronously.
        'store_errors': True,  # Store error info if task throws exception.
        'blocking': False,  # Poll the queue rather than do blocking pop.
        'connection': {
            'host': 'localhost',
            'port': 6379,
            'db': 0,
            'connection_pool': None,  # Definitely you should use pooling!
            # ... tons of other options, see redis-py for details.
    
            # huey-specific connection parameters.
            'read_timeout': 1,  # If not polling (blocking pop), use timeout.
            'max_errors': 1000,  # Only store the 1000 most recent errors.
            'url': None,  # Allow Redis config via a DSN.
        },
        'consumer': {
            'workers': 1,
            'worker_type': 'thread',
            'multiple_scheduler_locking': True,  # Prevent multiple periodic tasks by multiple schedulers.
            'initial_delay': 0.1,  # Smallest polling interval, same as -d.
            'backoff': 1.15,  # Exponential backoff using this rate, -b.
            'max_delay': 10.0,  # Max possible polling interval, -m.
            'utc': True,  # Treat ETAs and schedules as UTC datetimes.
            'scheduler_interval': 1,  # Check schedule every second, -s.
            'periodic': True,  # Enable crontab feature.
            'check_worker_health': True,  # Enable worker health checks.
            'health_check_interval': 1,  # Check worker health every second.
        }
    },
    'queue_name2': {
        'connection': {
            'connection_pool': ConnectionPool(host='localhost', port=6379, db=1)
        },
        'consumer': {
            'multiple_scheduler_locking': True,
            'workers': 2,
            'worker_type': 'thread',
        }
    },
}
```

The settings are almost the same as in [djhuey](https://huey.readthedocs.io/en/latest/contrib.html#setting-things-up)
Exceptions:
- You can only configure redis as storage engine.
- The `name` and `backend_class` parameters is not allowed.
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


### Collaborators

- [Update hueyx on PyPi](./update_version.md)