from django.db import models
from django.utils import timezone

from ..managers.devices import DeviceManager


class AbstractBaseDevice(models.Model):
    notification_service_proxy = None

    objects = DeviceManager()

    added_at = models.DateTimeField(default=timezone.now)
    modified_at = models.DateTimeField(auto_now=True)

    device_type = models.CharField(max_length=10, default=None)

    is_active = models.BooleanField(default=True)
    invalidated = models.BooleanField(default=False)

    class Meta:
        abstract = True

    def notify(self, *args, **kwargs):
        self.notification_service_proxy.send_message(
            recipient=self, *args, **kwargs)


class AndroidDeviceMixin(AbstractBaseDevice):
    app_id = models.CharField(max_length=16, default=None, null=True)
    device_token = models.CharField(max_length=64, blank=False, unique=True)
    development = models.BooleanField(default=False, null=False)

    class Meta:
        abstract = True


class IDeviceMixin(AbstractBaseDevice):
    registration_id = models.TextField(blank=True, unique=True)

    class Meta:
        abstract = True
