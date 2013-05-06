from copy import deepcopy
import functools


class MinimalMessagingTask:
    def __init__(self, **kwargs):
        pass

    def __call__(self, f):
        class WrappedTask:
            def __init__(self):
                self.request = self
                self.retries = 0

            def __call__(self, *args, **kwargs):
                self.args = deepcopy(args)
                self.kwargs = deepcopy(kwargs)
                return f(*args, **kwargs)

            def delay(self, f_self, *args, **kwargs):
                return self(*args, **kwargs)

            def apply_async(self, args, **kwargs):
                return self(*args[1:len(args)], **kwargs)

            def retry(self, **kwargs):
                self.retries += 1
                self(*self.args, **self.kwargs)

        return functools.wraps(f)(WrappedTask())

try:
    from celery import Celery
    from celery.utils.log import get_task_logger

    task = Celery().task

except ImportError:
    task = MinimalMessagingTask

    def get_task_logger(name):
        return
