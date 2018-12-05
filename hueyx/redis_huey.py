from functools import wraps
from django.db import close_old_connections
from huey import RedisHuey as RedisHueyOriginal


class RedisHuey(RedisHueyOriginal):
    """
    Extends the RedisHuey with new decorators which start a new transaction for every task.
    """
    def db_task(self, *args, **kwargs):
        def decorator(fn):
            ret = self.task(*args, **kwargs)(close_db(fn, self))
            ret.call_local = fn
            return ret
        return decorator

    def db_periodic_task(self, *args, **kwargs):
        def decorator(fn):
            return self.periodic_task(*args, **kwargs)(close_db(fn, self))
        return decorator


def close_db(fn, huey: RedisHuey):
    """Decorator to be used with tasks that may operate on the database."""
    @wraps(fn)
    def inner(*args, **kwargs):
        try:
            return fn(*args, **kwargs)
        finally:
            if not huey.always_eager:
                close_old_connections()
    return inner
