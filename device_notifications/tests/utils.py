from mock import patch

from django.test.testcases import TestCase

from device_notifications import settings
from device_notifications.models import AbstractBaseDevice


class ConcreteTestDevice(AbstractBaseDevice):
    pass


class DeviceNotificationTestCase(TestCase):
    def setUp(self):
        self.get_device_model_patcher = patch.object(
            settings,
            'get_device_model',
            return_value=ConcreteTestDevice)
        self.get_device_model_patcher.start()
        super(DeviceNotificationTestCase, self).setUp()

    def tearDown(self):
        super(DeviceNotificationTestCase, self).tearDown()
        self.get_device_model_patcher.stop()
