from gcmclient import GCM
from gcmclient import JSONMessage

from device_notifications.settings import GCM_API_KEY


def gcm_send_message(device, message, retry):
    gcm = GCM(GCM_API_KEY)

    gcm_message = JSONMessage([device.device_id], message)

    result = gcm.send(gcm_message)

    if result.canonical:
        # updated registration id
        device.device_id = result.canonical()[device.device_id]
        device.save()

    elif result.not_registered:
        # the user uninstalled the app
        device.invalidated = True
        device.save()

    elif result.failed:
        # unrecoverably failed
        device.invalidated = True
        device.save()

    elif result.needs_retry():
        # recoverably failed try again
        # import task here to avoid circular imports
        from device_notifications.tasks import gcm_send_message_task

        retry += 1

        gcm_send_message_task.apply_async(
            args=[
                device.device_id,
                message,
                retry
            ],
            countdown=result.delay(retry))
