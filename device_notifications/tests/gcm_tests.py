from mock import patch
from mock import MagicMock

from device_notifications.tests.utils import DeviceNotificationTestCase
from device_notifications.tests.utils import ConcreteTestDevice

from device_notifications.spi.gcm import gcm_send_message


class FakeGCMResponse(object):
    canonical = []
    not_registered = []
    failed = []
    needs_retry_ctl = False

    def needs_retry(self):
        return self.needs_retry_ctl


class GCMSendMessageTests(DeviceNotificationTestCase):
    def setUp(self):
        super(GCMSendMessageTests, self).setUp()
        gcm_mock = MagicMock(name='gcm')
        self.send_mock = gcm_mock.send

        self.GCM_patcher = patch(
            'device_notifications.spi.gcm.GCM',
            return_value=gcm_mock)
        self.GCM_patcher.start()

    def tearDown(self):
        self.GCM_patcher.stop()
        super(GCMSendMessageTests, self).tearDown()

    def test_basic_send_message(self):
        logger = MagicMock(name='logger')
        device = ConcreteTestDevice(device_id='testid')

        self.send_mock.return_value = FakeGCMResponse()

        gcm_send_message(device, 'test message', 0, logger)
        self.assertTrue(self.send_mock.called)
