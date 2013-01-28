class FallbackTask(object):
    def __call__(self, *args, **kwargs):
        pass

    def __getattr__(self, *args, **kwargs):
        return self.__call__

def fallback_task(*args, **kwargs):
    return FallbackTask(*args, **kwargs)

try:
    from celery.task import task
except ImportError:
    # If celery isn't available, provide a fallback_task as
    # an alternative
    task = fallback_task

