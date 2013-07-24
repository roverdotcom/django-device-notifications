from gcmclient import GCM
from gcmclient import JSONMessage

from device_notifications.settings import GCM_API_KEY
from device_notifications.settings import GCM_MAX_TRIES


def gcm_send_message(device, message, retry, logger):
    gcm = GCM(GCM_API_KEY)

    logdata = {
        'device_id': device.device_id,
        'message': message,
        'retry': retry,
    }

    logger.debug(
        ('Sending message "%(message)s" to device '
         '"%(device_id)s". This is try %(retry)d.'),
        logdata,
        extra=logdata)

    gcm_message = JSONMessage([device.device_id], message)

    result = gcm.send(gcm_message)

    if result.canonical:
        # updated registration id
        new_device_id = result.canonical()[device.device_id]

        logdata['device_id_new'] = new_device_id
        logger.info(
            'Updating device from "%(device_id)s" to "%(device_id_new)s".',
            logdata,
            extra=logdata)

        device.device_id = new_device_id
        device.save()

    elif result.not_registered:
        # the user uninstalled the app

        logger.warning(
            ('Invalidating device "%(device_id)s" '
             'because it is not registered with Google.'),
            logdata,
            extra=logdata)

        device.invalidated = True
        device.save()

    elif result.failed:
        # unrecoverably failed
        error_code = result.failed[device.device_id]

        logdata['error_code'] = error_code

        logger.error(
            ('Sending message "%(message)s" to device "%(device_id)s" '
             'failed with error code "%(error_code)s".'),
            logdata,
            extra=logdata)

        device.invalidated = True
        device.save()

    elif result.needs_retry():
        # recoverably failed try again
        # import task here to avoid circular imports
        from device_notifications.tasks import gcm_send_message_task

        retry += 1
        delay = result.delay(retry)

        logdata['retry'] = retry
        logdata['delay'] = delay
        logdata['threshold'] = GCM_MAX_TRIES

        if retry > GCM_MAX_TRIES:
            logger.error(
                ('Stopping trying to delive message "%(message)s"'
                 ' to device "%(device_id)s" because we reached the'
                 ' maximum try threshold of "%(threshold)d".'),
                logdata,
                extra=logdata)
            return None

        logger.info(
            ('Retrying sending of message "%(message)s" '
             'to device "%(device_id)s" for the "%(retry)d" time, '
             'waiting "%(delay)f" seconds.'),
            logdata,
            extra=logdata)

        gcm_send_message_task.apply_async(
            args=[
                device.pk,
                message,
                retry
            ],
            countdown=delay)
