from django.db import models

from django.utils import timezone

from django.conf import settings

from .managers import DeviceManager

from .spi import apn as apn_api
from .spi import gcm as gcm_api


class InvalidDeviceTypeException(Exception):
    """
    Exception raised when a device_type other
    than those supported is specified.
    """
    pass


class AbstractBaseDevice(models.Model):
    """
    This model may be used as a mixin, or the the child "Device" model
    may be used as-is.
    """
    objects = DeviceManager()

    DEVICE_TYPE_IOS = 'ios'
    DEVICE_TYPE_ANDROID = 'android'
    DEVICE_TYPE_CHOICES = (
        (DEVICE_TYPE_ANDROID, 'Android'),
        (DEVICE_TYPE_IOS, 'iOS')
    )

    device_type = models.CharField(
        max_length=10,
        choices=DEVICE_TYPE_CHOICES)

    development = models.BooleanField(default=False, null=False)

    added_at = models.DateTimeField(default=timezone.now)
    modified_at = models.DateTimeField(auto_now=True)

    is_active = models.BooleanField(
        default=True)
    invalidated = models.BooleanField(
        default=False)

    app_id = models.CharField(max_length=16, default=None, null=True)
    device_id = models.CharField(
        max_length=64,
        blank=False,
        unique=True)
    registration_id = models.TextField(
        blank=True,
        unique=True)

    class Meta:
        abstract = True

    def send_message(self, message, app_id=None):
        if self.device_type == self.DEVICE_TYPE_IOS:
            return apn_api.send_message(self, message, app_id)
        elif self.device_type == self.DEVICE_TYPE_ANDROID:
            return gcm_api.send_message(self, message)
        else:
            raise InvalidDeviceTypeException()


class Device(AbstractBaseDevice):
    user = models.ForeignKey(
        getattr(settings, 'AUTH_USER_MODEL', 'auth.User'),
        blank=True,
        null=True)
