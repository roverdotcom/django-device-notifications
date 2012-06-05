from django.db import models

from tasks import notify_idevices
from settings import APN_DEFAULT_APP_ID

class IDeviceManager(models.Manager):

    def notify_ios_app(self, msg, app_id=APN_DEFAULT_APP_ID, person=None):
        if person is None or app_id is None:
            raise ValueError('Expect parameter "device" or "person" and "app_id".')
    
        devices = [d.token for d
                    in self.filter(person=person, app_id=app_id)]

        notify_idevices.delay(msg, devices, app_id)
