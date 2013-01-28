from django.db import models
from django.db.models.query import QuerySet

from task import task

class DeviceQuerySet(QuerySet):
    @task
    def send_message(self, msg, app_id=None):    
        for device in self.all():
            if not device.invalidated:
                device.send_message(msg, app_id)

class DeviceManager(models.Manager):
    def get_query_set(self):
        return DeviceQuerySet(self.model)
