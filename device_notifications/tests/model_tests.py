from mock import patch

from django.test.testcases import TestCase

from device_notifications import settings

from device_notifications.models import AbstractBaseDevice
from device_notifications.models import InvalidDeviceType


class ConcreteTestDevice(AbstractBaseDevice):
    pass


class AbstractBaseDeviceSendMessageTests(TestCase):
    def setUp(self):
        self.get_device_model_patcher = patch.object(
            settings,
            'get_device_model',
            return_value=ConcreteTestDevice)
        self.get_device_model_patcher.start()
        super(AbstractBaseDeviceSendMessageTests, self).setUp()

    def tearDown(self):
        super(AbstractBaseDeviceSendMessageTests, self).tearDown()
        self.get_device_model_patcher.stop()

    @patch('device_notifications.models.gcm_send_message_task')
    def test_send_message(self, gcm_send_message_task):
        device = ConcreteTestDevice(
            pk=1,
            device_type='android')
        message = 'Hello World'

        device.send_message(message)

        gcm_send_message_task.apply_async.assert_called_with(
            args=[device.pk, message])

    def test_bad_device_type(self):
        device = ConcreteTestDevice(device_type='windows_phone')

        self.assertRaises(InvalidDeviceType, device.send_message, 'Hi')

    @patch('device_notifications.models.gcm_send_message_task')
    def test_does_not_send_to_invalidated_devices(self, gcm_send_message_task):
        device = ConcreteTestDevice(
            device_type='android',
            invalidated=True)

        device.send_message('test')

        self.assertFalse(gcm_send_message_task.apply_async.called)

    @patch('device_notifications.models.gcm_send_message_task')
    def test_does_not_send_to_inactive_devices(self, gcm_send_message_task):
        device = ConcreteTestDevice(
            device_type='android',
            is_active=False)

        device.send_message('test')

        self.assertFalse(gcm_send_message_task.apply_async.called)

    @patch('device_notifications.models.gcm_send_message_task')
    def test_does_not_send_to_inactive_and_invalidated_devices(self, gcm_send_message_task):
        device = ConcreteTestDevice(
            device_type='android',
            is_active=False)

        device.send_message('test')

        self.assertFalse(gcm_send_message_task.apply_async.called)
