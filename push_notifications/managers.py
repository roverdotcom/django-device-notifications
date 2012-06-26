from django.db import models

from tasks import notify_idevices
from settings import APN_DEFAULT_APP_ID

class IDeviceManager(models.Manager):

    def notify_ios_app(self, msg, app_id=APN_DEFAULT_APP_ID, person=None):
        if person is None or app_id is None:
            raise ValueError('Expect parameter "device" or "person" and "app_id".')
    
        development_devices = [d.token for d in self.filter(
                person=person, app_id=app_id, 
                invalidated=False, development=True)]
        notify_idevices.delay(msg, development_devices, app_id, 
                        development=True)

        production_devices = [d.token for d in self.filter(
                person=person, app_id=app_id, 
                invalidated=False, development=False)]
        notify_idevices.delay(msg, production_devices, app_id)
