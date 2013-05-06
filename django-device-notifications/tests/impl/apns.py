import os

from unittest import TestCase

from ...impl.apns import ApnsProxy
from ...impl.apns import ApnsRequest
from ...impl.apns import ApnsRecipient
from ...impl.apns import ApnsConnectionContextManager

RequestInitErrors = ApnsRequest.InitErrors
ConnectionContextManagerInitErrors = ApnsConnectionContextManager.InitErrors

from ...test.utils import A_LOGGER

A_STRING = 'a'
A_FILE_PATH = os.path.abspath(__file__)
NOT_A_STRING = 1
NOT_A_DICT = 1
NOT_CASTABLE_TO_INT = 'a'


class MockApnsConnectionContextManager(ApnsConnectionContextManager):
    entered = False
    sent = None

    def init_context(self, *args):
        self.connection = self

    def __enter__(self):
        self.entered = True
        return self.connection

    def send(self, string):
        self.sent = string

    def close(self):
        pass


class MockApnsProxy(ApnsProxy):
    connection_context_manager_class = MockApnsConnectionContextManager


class ApnsProxyInitTests(TestCase):
    def test_with_bad_args(self):
        try:
            ApnsProxy(NOT_A_DICT, NOT_A_STRING)
            self.assertFalse(True)
        except ApnsProxy.InitErrors as e:
            self.assertEqual(e, {'logger': e.NOT_LOGGER,
                                 'connection_contexts_by_app_id': e.NOT_DICT,
                                 'password': e.NOT_STRING})

        try:
            MockApnsProxy({
                NOT_A_STRING:
                    MockApnsConnectionContextManager(True, A_FILE_PATH),
                'a': None,
                'b': {'bad_arg': None},
                'c': {'cert_path': NOT_A_STRING,
                      'key_path': NOT_A_STRING},
                'd': {'cert_path': '!',
                      'password': NOT_A_STRING},
                'e': {'cert_path': A_FILE_PATH,
                      'key_path': A_FILE_PATH,
                      'password': A_STRING}},
              logger=A_LOGGER)
            self.assertFalse(True)
        except ApnsProxy.InitErrors as e:
            self.assertEqual(
                e,
                {'connection_contexts_by_app_id': {
                    NOT_A_STRING: e.NOT_STRING,
                    'a':
                        e.NOT_CONNECTION_CONTEXT_FORMAT.format(
                            cls=MockApnsConnectionContextManager),
                    'b': {
                        'bad_arg':
                            ConnectionContextManagerInitErrors.UNKNOWN_KEY,
                        'cert_path':
                            ConnectionContextManagerInitErrors.NOT_PROVIDED},
                    'c': {
                        'cert_path':
                            ConnectionContextManagerInitErrors.NOT_STRING,
                        'key_path':
                            ConnectionContextManagerInitErrors.NOT_STRING},
                    'd': {
                        'cert_path':
                            ConnectionContextManagerInitErrors.NOT_FILE,
                        'password':
                            ConnectionContextManagerInitErrors.NOT_STRING}}})


class ApnsRequestInitTests(TestCase):
    def test_with_bad_args(self):
        try:
            ApnsRequest(**{'body': NOT_A_STRING,
                           'badge': NOT_CASTABLE_TO_INT,
                           'sound': NOT_A_STRING,
                           'payload': NOT_A_DICT,
                           'logger': A_LOGGER})
            self.assertFalse(True)
        except ApnsRequest.InitErrors as e:
            self.assertEqual(e, {'body': e.NOT_STRING,
                                'badge': e.CANT_TO_INT,
                                'sound': e.WRONG_SOUND_FORMAT,
                                'payload': e.NOT_DICT})

        try:
            ApnsRequest(payload={'aps': None}, logger=A_LOGGER)
            self.assertFalse(True)
        except ApnsRequest.InitErrors as e:
            self.assertEqual(e['payload'], {'aps': e.NOT_DICT})

        try:
            ApnsRequest(payload={'aps': {'alert': None}}, logger=A_LOGGER)
            self.assertFalse(True)
        except ApnsRequest.InitErrors as e:
            self.assertEqual(e['payload']['aps'], {'alert': e.ALERT_TYPE})

        ApnsRequest(body=A_STRING, payload={'aps': {'alert': A_STRING}},
                    logger=A_LOGGER)


APP_ID_1 = 'app_id_1'
APP_ID_2 = 'app_id_2'
APP_ID_3 = 'app_id_3'


class MockApnsRecipient(object):
    def __init__(self, app_id=APP_ID_1):
        self.app_id = app_id

    app_id = None
    device_token = '020406080A0C0E10121416181A1C1E20'
    is_active = True
    invalidated = False
    development = True


class ApnsProxySendTests(TestCase):
    def setUp(self):
        connection_context_manager_1 = (
            MockApnsConnectionContextManager(True, A_FILE_PATH))
        connection_context_manager_2 = (
            MockApnsConnectionContextManager(True, A_FILE_PATH))
        connection_context_manager_3 = (
            MockApnsConnectionContextManager(True, A_FILE_PATH))
        self.apns = MockApnsProxy({APP_ID_1: connection_context_manager_1,
                                   APP_ID_2: connection_context_manager_2,
                                   APP_ID_3: connection_context_manager_3},
                                  logger=A_LOGGER)

    def test_handles_app_id(self):
        apns = self.apns
        request = (
            ApnsRequest(body=A_STRING, payload={'aps': {'alert': A_STRING}},
                        logger=A_LOGGER))
        recipients = (MockApnsRecipient(), MockApnsRecipient(APP_ID_2))

        apns.send_message(request=request, recipients=recipients)

        self.assertTrue(apns.connection_contexts_by_app_id[APP_ID_1].entered)
        self.assertTrue(apns.connection_contexts_by_app_id[APP_ID_2].entered)
        self.assertFalse(apns.connection_contexts_by_app_id[APP_ID_3].entered)

    def test_get_packed_bytes(self):
        apns = self.apns
        request = (
            ApnsRequest(body=A_STRING, payload={'aps': {'alert': A_STRING}},
                        logger=A_LOGGER))
        recipient = MockApnsRecipient()

        apns.send_message(request=request, recipient=recipient)

        self.assertTrue(apns.connection_contexts_by_app_id[APP_ID_1].entered)

        expected_sent_message = chr(0)
        expected_sent_message += chr(0) + chr(32)
        expected_sent_message += (
            ''.join((chr(i) for i in xrange(2, 32 + 2, 2))))
        expected_sent_message += chr(0) + chr(23)
        expected_sent_message += '{"aps": {"alert": "' + A_STRING + '"}}'
        self.assertEqual(apns.connection_contexts_by_app_id[APP_ID_1].sent,
                         expected_sent_message)
