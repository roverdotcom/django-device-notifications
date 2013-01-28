import os, copy, binascii

from django.contrib.auth.models import User

from django.test.testcases import TestCase

from models import DeviceManager, IDevice
from settings import APN_PORT, APN_HOST, APN_CERTIFICATE, APN_KEY, APN_PASSPHRASE
from settings import APN_DEFAULT_APP_ID, APN_CERT_PATH_TEMPLATE

from spi.apn import IDEVICE_NOTIFICATION_TEMPLATE
from spi.apn import _create_apn_connection, _pack_message, _notify_idevices, _truncate_string

SAMPLE_DEVICE_TOKEN = \
        '740faaaaaaaaf74f9b7c25d48e3358945f6aa01da5ddb387462c7eaf61bb78ad'

SAMPLE_DEVICE_TOKEN_1 = \
        '740faaaaaaaaf74f9b7c25d48e3358945f6aa01da5ddb387462ceeeeeeeeeeee'

SAMPLE_PACKET = \
        '000020740faaaaaaaaf74f9b7c25d48e3358945f6aa01da5ddb387462c7eaf61bb78ad00ff7b22617073223a207b226261646765223a20312c2022616c657274223a207b22626f6479223a202261626361626361626361626361626361626361626361626361626361626361626361626361626361626361626361626361626361626361626361626361626361626361626361626361626361626361626361626361626361626361626361626361626361626361626361626361626361626361626361626361626361626361626361626361626361626361626361626361626361626361626361626361626361626361626361626361626361626361626361626361622e2e2e222c2022616374696f6e2d6c6f632d6b6579223a20224f70656e227d7d7d' 

class SendMessageTest(TestCase):
    
    def setUp(self):
        super(SendMessageTest, self).setUp()

    def test_model(self):
        """
            This test need to be modified to remove `person` before
            release to open-source
        """
        user = User(username='gooduser', first_name='Good', last_name='User')

        prod_device = IDevice(user=user, token=SAMPLE_DEVICE_TOKEN)
        prod_device.save()
        
        dev_device = IDevice(person=person, token=SAMPLE_DEVICE_TOKEN_1, 
                app_id=APN_DEFAULT_APP_ID, development=True)
        dev_device.save()
        
        IDevice.objects.notify_ios_app('Hello World', 
                app_id=APN_DEFAULT_APP_ID, person=person)

    def test_settings(self):
        # This test is here to assert env is setup properly
        self.assertIsNotNone(APN_PORT)
        self.assertIsNotNone(APN_HOST)
        self.assertIsNotNone(APN_PASSPHRASE)
        self.assertIsNotNone(APN_CERT_PATH_TEMPLATE)
        
        app_id = APN_DEFAULT_APP_ID
        self.assertIsNotNone(app_id)
  
        cert_path = APN_CERT_PATH_TEMPLATE % (app_id + '-cert')
        key_path = APN_CERT_PATH_TEMPLATE % (app_id + '-key')

        self.assertTrue(os.path.exists(cert_path))
        self.assertTrue(os.path.exists(key_path))

    def test_pack_message(self):
        # normal packet
        packed = _pack_message(IDEVICE_NOTIFICATION_TEMPLATE, SAMPLE_DEVICE_TOKEN)
        self.assertIsNotNone(packed, 'Expected non-None binary')
        self.assertTrue(len(packed) > 32, 'Expected non-None binary')

        self.assertTrue(len(packed) < 294, 'Expected smaller binary packet')

        hex_string = packed.encode('hex')
        self.assertTrue(hex_string.index(SAMPLE_DEVICE_TOKEN) > 0, 'Expect device token.')

        # really large packet
        large_message = copy.deepcopy(IDEVICE_NOTIFICATION_TEMPLATE)
        large_message['aps']['alert']['body'] = \
            ''.join(['abc' for i in range(0, 1000)])        
        packed = _pack_message(large_message, SAMPLE_DEVICE_TOKEN)
        self.assertIsNotNone(packed, 'Expected non-None binary')
        self.assertTrue(len(packed) > 32, 'Expected non-None binary')
        self.assertTrue(len(packed) < 294, 'Expected smaller binary packet')

        hex_string = packed.encode('hex')
        self.assertTrue(hex_string.index(SAMPLE_DEVICE_TOKEN) > 0, 'Expect device token.')

    def test_create_connect_to_apn(self):
        apn_host = APN_HOST
        apn_port = APN_PORT
        app_id = APN_DEFAULT_APP_ID
        cert_path = APN_CERT_PATH_TEMPLATE % (app_id + '-cert')
        key_path = APN_CERT_PATH_TEMPLATE % (app_id + '-key')
        passphrase = APN_PASSPHRASE

        c = _create_apn_connection(apn_host, apn_port, key_path, 
                                  cert_path, passphrase)
        data = binascii.unhexlify(SAMPLE_PACKET)
        c.send(data)

    def test_send_notification(self):
        app_id = APN_DEFAULT_APP_ID

        _notify_idevices(IDEVICE_NOTIFICATION_TEMPLATE, 
                        [SAMPLE_DEVICE_TOKEN], app_id)

        _notify_idevices(IDEVICE_NOTIFICATION_TEMPLATE, 
                        [SAMPLE_DEVICE_TOKEN], app_id, 
                        development=True)
