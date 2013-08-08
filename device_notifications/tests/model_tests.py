from mock import patch

from django.test.testcases import TestCase

from device_notifications import settings

from device_notifications.models import AbstractBaseDevice
from device_notifications.models import InvalidDeviceType


class ConcreteTestDevice(AbstractBaseDevice):
    pass


@patch.object(settings, 'get_device_model', return_value=ConcreteTestDevice)
class AbstractBaseDeviceTests(TestCase):
    @patch('device_notifications.models.gcm_send_message_task')
    def test_send_message(self, gcm_send_message_task):
        device = ConcreteTestDevice(
            pk=1,
            device_type='android')
        message = 'Hello World'

        device.send_message(message)

        gcm_send_message_task.apply_async.assert_called_with(
            args=[device.pk, message])

    @patch('device_notifications.models.gcm_send_message_task')
    def test_send_message_bad_device_type(self, gcm_send_message_task):
        device = ConcreteTestDevice(
            pk=1,
            device_type='windows_phone')

        self.assertRaises(InvalidDeviceType, device.send_message, 'Hi')
