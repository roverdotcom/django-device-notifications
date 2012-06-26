from django.db import models

from people.models import Person
from managers import IDeviceManager

APP_ID_CHOICES = (
    ('com.rover.Rover-com', 'com.rover.Rover-com'),
)

class IDevice(models.Model):
    objects = IDeviceManager()

    person = models.ForeignKey(Person, related_name='idevices')
    development = models.BooleanField(default=False, null=False)
    token = models.CharField(max_length=64,
            default='',null=False, blank=False, unique=True)
    app_id = models.CharField(max_length=64,
            default='',null=False, blank=False,
            choices=APP_ID_CHOICES)
    invalidated = models.BooleanField(default=False,
            verbose_name='The token is invalidated by APN')
