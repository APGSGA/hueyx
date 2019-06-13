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
        'connection': {
            'host': 'localhost',
            'port': 6379,
            'db': 0,
        },
        'consumer': {
            'workers': 1,
            'worker_type': 'process',
        }
    },
    'queue_name2': {
        'connection': {
            'connection_pool': ConnectionPool(host='localhost', port=6379, db=1)
        },
        'consumer': {
            'multiple_scheduler_locking': True,
            'prometheus_metrics': True,
            'workers': 2,
            'worker_type': 'thread',
        }
    },
}
```

The settings are almost the same as in djhuey.
Have a look at the [huey documentation](https://huey.readthedocs.io/en/latest/contrib.html#setting-things-up) 
to see the exact parameter usage.

Exceptions:
- You can only configure redis as storage engine.
- The `name` and `backend_class` parameters are not supported.
- The options `multiple_scheduler_locking` and `prometheus_metrics_enabled` have been added. See below.
- The parameter `heartbeat_timeout` for `db_task` has been added. See below.

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
    
@HUEY_Q2.db_task(heartbeat_timeout=120)
def my_heartbeat_task(heartbeat: Heartbeat):
    with heartbeat.long_running_operation():
        print('This operation can take a while -> don\'t check for heartbeats')
    print('Now we check for heartbeats -> call heartbeat() periodically')
    heartbeat()
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

#### Prometheus integration
Prometheus will export the metric `hueyx_task_events` which counts huey signals.
You have to implement [django-prometheus](https://github.com/korfuri/django-prometheus).

```python
# Add to installed apps in settings.py
INSTALLED_APPS = [
    ...,
    'hueyx',
    'django_prometheus',
    ...
]

PROMETHEUS_METRICS_EXPORT_PORT = 8001
PROMETHEUS_METRICS_EXPORT_ADDRESS = ''
```

The metrics will be available on [localhost:8001/metrics](http://localhost:8001/metrics) as soon as the hueyx consumer
has been started.

##### Multi process mode
Prometheus is not been built for the way python handles multi processing. Therefore, we have to make additional work to let it 
run if you use `'worker_type': 'process'`.

As a workaround, Prometheus provides a [multiprocess mode](https://github.com/prometheus/client_python#multiprocess-mode-gunicorn)
where the workers save their metrics into a shared folder and a small web server reads them and provides the metrics 
for all workers.

###### A - General
Provide a shared folder in the environment variable `prometheus_multiproc_dir`.

For example
```bash
export prometheus_multiproc_dir="/home/severin/Documents/mpd_prometheus"
```

###### B - Huey consumer

Adjust the settings.py
```python
# settings.py
# PROMETHEUS_METRICS_EXPORT_PORT = 8001
PROMETHEUS_METRICS_EXPORT_PORT_RANGE = range(8001, 8050) # Use a range which has not been used before.
PROMETHEUS_METRICS_EXPORT_ADDRESS = ''
```
With the settings above, we make sure every worker process is running on its own port.
Also, make sure you start the consumer with the shared folder env variable.

###### C - Web server
Hueyx provides a preconfigured web server which you can just start.

```bash
# The here defined port is the one you actually want to pull for the metrics.
./manage.py run_hueyx_prometheus --port 9100
```

The metrics will be reachable on `http://localhost:9100`.


##### Heartbeat tasks
Heartbeat tasks are tasks with the parameter `heartbeat_timeout`. It defines the timeout in seconds. 
They get a Heartbeat object which needs to be called in order to send a heartbeat to redis. 
If no heartbeat occurs in set timeout the task is presumed to be dead and will automatically get restarted. 
`heartbeat_timeout` needs to be at least 120 seconds. It does not work together with the parameter `include_task`.

### Additional settings

##### multiple_scheduler_locking
`multiple_scheduler_locking` has been added to support multiple huey schedulers.
If you run huey in a cloud environment, you will end up running multiple huey instances which each will
schedule the periodic task.
`multiple_scheduler_locking` prevents periodic tasks to be scheduled multiple times. It is false by default.


### Collaborators

- [Update hueyx on PyPi](./update_version.md)