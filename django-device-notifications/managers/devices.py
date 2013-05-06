from django.db import models
from django.db.models.query import QuerySet


class DeviceQuerySet(QuerySet):
    def notify(self, *args, **kwargs):
        self.model.notification_service_proxy.send_message(
            recipients=self, *args, **kwargs)


class DeviceManager(models.Manager):
    def get_query_set(self):
        return DeviceQuerySet(self.model)
