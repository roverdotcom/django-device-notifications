from django.db import models

from people.models import Person
from .managers import DeviceManager
from .managers import IDeviceManager

APP_ID_CHOICES = (
    ('com.rover.Rover-com', 'com.rover.Rover-com'),
)


DEVICE_TYPE_CHOICES = (
    ('android', 'Android'),
    ('ios', 'iOS')
)


class DeviceBase(models.Model):
    objects = DeviceManager()

    is_development = models.BooleanField(default=False)

    device_type = models.CharField(
        max_length=10,
        choices=DEVICE_TYPE_CHOICES)
    device_id = models.CharField(
        max_length=64,
        blank=False,
        unique=True)
    registration_id = models.TextField(
        blank=True,

    added_at = models.DateTimeField(default=timezone.now)
    modified_at = models.DateTimeField(auto_now=True)

    is_active = models.BooleanField(
        default=True)

    class Meta:
        abstract = True

    def send_message(self, message):
        pass


class IDevice(models.Model):
    objects = IDeviceManager()

    person = models.ForeignKey(Person, related_name='idevices')
    development = models.BooleanField(default=False, null=False)

    token = models.CharField(max_length=64,
            default='',null=False, blank=False, unique=True)
    app_id = models.CharField(max_length=64,
            default='',null=False, blank=False,
            verbose_name='The token is invalidated by APN')
