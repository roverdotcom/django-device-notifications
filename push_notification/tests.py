import os, settings,  copy,  binascii

from django.test.testcases import TestCase
from tasks import IDEVICE_NOTIFICATION_TEMPLATE, \
    pack_message, create_apn_connection, notify_idevices

SAMPLE_DEVICE_TOKEN = \
        '740faaaaaaaaf74f9b7c25d48e3358945f6aa01da5ddb387462c7eaf61bb78ad'

SAMPLE_PACKET = \
        '000020740faaaaaaaaf74f9b7c25d48e3358945f6aa01da5ddb387462c7eaf61bb78ad00ff7b22617073223a207b226261646765223a20312c2022616c657274223a207b22626f6479223a202261626361626361626361626361626361626361626361626361626361626361626361626361626361626361626361626361626361626361626361626361626361626361626361626361626361626361626361626361626361626361626361626361626361626361626361626361626361626361626361626361626361626361626361626361626361626361626361626361626361626361626361626361626361626361626361626361626361626361626361626361622e2e2e222c2022616374696f6e2d6c6f632d6b6579223a20224f70656e227d7d7d' 
        
class TaskTest(TestCase):
    
    def setUp(self):
        super(TaskTest, self).setUp()

    def test_settings(self):
        # This test is here to assert env is setup properly
        self.assertIsNotNone(settings.APN_PORT)
        self.assertIsNotNone(settings.APN_HOST)
        self.assertIsNotNone(settings.APN_PASSPHRASE)
        self.assertIsNotNone(settings.APN_CERT_PATH_TEMPLATE)
        
        app_id = settings.APN_DEFAULT_APP_ID
        self.assertIsNotNone(app_id)
  
        cert_path = settings.APN_CERT_PATH_TEMPLATE % (app_id + '-cert')
        key_path = settings.APN_CERT_PATH_TEMPLATE % (app_id + '-key')

        self.assertTrue(os.path.exists(cert_path))
        self.assertTrue(os.path.exists(key_path))

    def test_pack_message(self):
        # normal packet
        packed = pack_message(IDEVICE_NOTIFICATION_TEMPLATE, SAMPLE_DEVICE_TOKEN)
        self.assertIsNotNone(packed, 'Expected non-None binary')
        self.assertTrue(len(packed) > 32, 'Expected non-None binary')

        self.assertTrue(len(packed) < 294, 'Expected smaller binary packet')
        
        hex_string = packed.encode('hex')
        self.assertTrue(hex_string.index(SAMPLE_DEVICE_TOKEN) > 0, 'Expect device token.')
        
        # really large packet
        large_message = copy.deepcopy(IDEVICE_NOTIFICATION_TEMPLATE)
        large_message['aps']['alert']['body'] = \
            ''.join(['abc' for i in range(0, 1000)])        
        packed = pack_message(large_message, SAMPLE_DEVICE_TOKEN)
        self.assertIsNotNone(packed, 'Expected non-None binary')
        self.assertTrue(len(packed) > 32, 'Expected non-None binary')
        self.assertTrue(len(packed) < 294, 'Expected smaller binary packet')
        
        hex_string = packed.encode('hex')
        self.assertTrue(hex_string.index(SAMPLE_DEVICE_TOKEN) > 0, 'Expect device token.')
    
    def test_create_connect_to_apn(self):
        app_id = settings.APN_DEFAULT_APP_ID
        cert_path = settings.APN_CERT_PATH_TEMPLATE % (app_id + '-cert')
        key_path = settings.APN_CERT_PATH_TEMPLATE % (app_id + '-key')
        passphrase = settings.APN_PASSPHRASE
        
        c = create_apn_connection(key_path, cert_path, passphrase)
        data = binascii.unhexlify(SAMPLE_PACKET)
        c.send(data)

    def test_send_notification(self):
        app_id = settings.APN_DEFAULT_APP_ID

        notify_idevices(IDEVICE_NOTIFICATION_TEMPLATE, 
                        [SAMPLE_DEVICE_TOKEN], app_id)

