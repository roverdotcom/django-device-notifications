from django.db import models
from django.utils import timezone

from .tasks import gcm_send_message_task


class InvalidDeviceType(ValueError):
    """
    Exception raised when a device_type other
    than those supported is specified.
    """
    pass


class AbstractBaseDevice(models.Model):
    """
    You should make a subclass of this model that links to your User model.
    """

    DEVICE_TYPE_ANDROID = 'android'
    DEVICE_TYPE_CHOICES = (
        (DEVICE_TYPE_ANDROID, 'Android'),
    )

    device_type = models.CharField(
        max_length=10,
        choices=DEVICE_TYPE_CHOICES)

    added_at = models.DateTimeField(default=timezone.now)
    modified_at = models.DateTimeField(auto_now=True)

    is_active = models.BooleanField(
        default=True)
    invalidated = models.BooleanField(
        default=False)

    app_id = models.CharField(
        max_length=16,
        default=None,
        null=True)

    device_id = models.TextField()

    class Meta:
        abstract = True
        unique_together = ('device_type', 'device_id')

    def send_message(self, message):
        if self.device_type == self.DEVICE_TYPE_ANDROID:
            return gcm_send_message_task(self.pk, message)

        else:
            raise InvalidDeviceType(
                '{} is not supported.'.format(self.get_device_type_display()))
