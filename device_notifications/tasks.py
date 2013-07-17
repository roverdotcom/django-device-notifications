from celery.task import task

from .spi.gcm import gcm_send_message

from .settings import DEVICE_MODEL


@task
def gcm_send_message_task(device_id, message):
    device = DEVICE_MODEL.objects.get(pk=device_id)
    gcm_send_message(device, message)
