from django.db import models

from people.models import Person
from .managers import DeviceManager
from .managers import IDeviceManager

from .api import apn as apn_api
from .api import gcm as gcm_api


class DeviceBase(models.Model):
    objects = DeviceManager()

    is_development = models.BooleanField(default=False)

    DEVICE_TYPE_IOS = 'ios'
    DEVICE_TYPE_ANDROID = 'android'
    DEVICE_TYPE_CHOICES = (
        (DEVICE_TYPE_ANDROID, 'Android'),
        (DEVICE_TYPE_IOS, 'iOS')
    )
    device_type = models.CharField(
        max_length=10,
        choices=DEVICE_TYPE_CHOICES)

    device_id = models.CharField(
        max_length=64,
        blank=False,
        unique=True)
    registration_id = models.TextField(
        blank=True,
        unique=True)

    added_at = models.DateTimeField(default=timezone.now)
    modified_at = models.DateTimeField(auto_now=True)

    is_active = models.BooleanField(
        default=True)
    invalidated = models.BooleanField(
        default=False)

    class Meta:
        abstract = True

    def send_message(self, message):
        if self.device_type == self.DEVICE_TYPE_IOS:
            return apn_api.send_message(message)
        elif self.device_type == self.DEVICE_TYPE_ANDROID:
            return gcm_api.send_message(message)
        else:
            raise InvalidDeviceTypeException()


class IDevice(models.Model):
    objects = IDeviceManager()

    person = models.ForeignKey(Person, related_name='idevices')
    development = models.BooleanField(default=False, null=False)

    token = models.CharField(max_length=64,
            default='',null=False, blank=False, unique=True)
