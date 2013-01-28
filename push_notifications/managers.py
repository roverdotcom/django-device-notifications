from django.db import models

class DeviceManager(models.Manager):

    class DeviceQuerySet(models.query.QuerySet):
        def send_message(self, msg):    
            for device in devices:
                if not device.invalidated:
                    device.send_message(msg, development=True)

    def get_query_set(self):
        return DeviceQuerySet(self.model)
