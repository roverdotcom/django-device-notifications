from celery.task import task

from .spi.gcm import gcm_send_message

from .settings import get_device_model


@task
def gcm_send_message_task(device_pk, message, retry=0):
    device = get_device_model().objects.get(pk=device_pk)
    logger = gcm_send_message_task.get_logger()
    gcm_send_message(device, message, retry, logger)
