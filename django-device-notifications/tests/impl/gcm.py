from datetime import datetime
from math import isnan
from unittest import TestCase

from ...impl.gcm import GcmProxy
from ...impl.gcm import GcmRequest

RequestInitErrors = GcmRequest.InitErrors

from ...utils import FLOATS_TO_JSON_STRINGS

from ...test.utils import A_LOGGER


class MockRecipient(object):
    is_active = True
    invalidated = False

    _registration_id = None
    next_registration_id = 0

    @property
    def registration_id(self):
        if self._registration_id:
            return self._registration_id
        else:
            self._registration_id = str(MockRecipient.next_registration_id)
            MockRecipient.next_registration_id += 1

AN_ACCEPTABLE_RECIPIENT = MockRecipient()

SOMETHING_JSON_SERIALIZABLE = 'a'
SOMETHING_NOT_JSON_SERIALIZABLE = object()

A_STRING = 'a'
NOT_A_STRING = 1
NOT_A_BOOL = 1
NOT_A_DICT = 1
SOMETHING_NOT_INT_CASTABLE = 'a'


class GcmProxySendTests(TestCase):
    def setUp(self):
        self.gcm = GcmProxy('', logger=A_LOGGER)

    def test_with_bad_args(self):
        gcm = self.gcm

        try:
            gcm.send_message(recipient=AN_ACCEPTABLE_RECIPIENT,
                             data=NOT_A_DICT,
                             collapse_key=NOT_A_STRING,
                             delay_while_idle=NOT_A_BOOL,
                             time_to_live=SOMETHING_NOT_INT_CASTABLE,
                             restricted_package_name=NOT_A_STRING,
                             retries=SOMETHING_NOT_INT_CASTABLE)
            self.assertFalse(True)
        except gcm.SendMessageErrors as e:
            self.assertEqual(
                e, {'retries': e.CANT_TO_INT,
                    'request': {
                        'data': RequestInitErrors.NOT_DICT,
                        'collapse_key': RequestInitErrors.NOT_STRING,
                        'delay_while_idle':
                            RequestInitErrors.NOT_INSTANCE_FORMAT.format(
                                cls=bool),
                        'time_to_live': RequestInitErrors.CANT_TO_INT,
                        'restricted_package_name':
                            RequestInitErrors.NOT_STRING}})

    def test_with_bad_data(self):
        gcm = self.gcm

        try:
            gcm.send_message(
                recipient=AN_ACCEPTABLE_RECIPIENT,
                data={'from': SOMETHING_JSON_SERIALIZABLE,
                      'google.' + A_STRING: SOMETHING_JSON_SERIALIZABLE,
                      NOT_A_STRING: SOMETHING_JSON_SERIALIZABLE,
                      A_STRING: SOMETHING_NOT_JSON_SERIALIZABLE})
            self.assertFalse(True)
        except gcm.SendMessageErrors as e:
            self.assertEqual(
                e['request']['data'],
                {'from': RequestInitErrors.RESERVED_DATA_KEY,
                 'google.' + A_STRING:
                     RequestInitErrors.RESERVED_GOOGLE_DATA_KEY,
                 NOT_A_STRING: RequestInitErrors.NOT_STRING,
                 A_STRING:
                     RequestInitErrors.DATA_VALUE_CANT_TO_JSON_FORMAT.format(
                         value=SOMETHING_NOT_JSON_SERIALIZABLE)})

    def test_with_too_long_data(self):
        gcm = self.gcm

        excess_length = 1
        too_long_data_key = 'a' * (GcmRequest.MAX_DATA_LENGTH + 1)

        try:
            gcm.send_message(recipient=AN_ACCEPTABLE_RECIPIENT,
                             data={too_long_data_key: ''})
            self.assertFalse(True)
        except gcm.SendMessageErrors as e:
            self.assertEqual(e['request'].excess_length, excess_length)

        if GcmRequest.MAX_DATA_LENGTH >= 10:
            too_long_data = dict((str(i), '') for i in xrange(10))
            j = 0
            for i in xrange(GcmRequest.MAX_DATA_LENGTH - 9):
                too_long_data[str(j)] += 'a'
                j_plus_one = j + 1
                j = j_plus_one if j_plus_one < 10 else 0

            try:
                gcm.send_message(recipient=AN_ACCEPTABLE_RECIPIENT,
                                 data=too_long_data)
                self.assertFalse(True)
            except gcm.SendMessageErrors as e:
                self.assertEqual(e['request'].excess_length, excess_length)

    def test_with_float_values(self):
        gcm_request = GcmRequest(logger=A_LOGGER)

        value = float('nan')
        data = {A_STRING: value}
        gcm_request._set_data_or_errors(locals(), locals(), None)
        self.assertEqual(data, {A_STRING: FLOATS_TO_JSON_STRINGS[isnan]})

        value = float('inf')
        data[A_STRING] = value
        gcm_request._set_data_or_errors(locals(), locals(), None)
        self.assertEqual(data, {A_STRING: FLOATS_TO_JSON_STRINGS[value]})

        value = float('-inf')
        data[A_STRING] = value
        gcm_request._set_data_or_errors(locals(), locals(), None)
        self.assertEqual(data, {A_STRING: FLOATS_TO_JSON_STRINGS[value]})

    def test_response(self):
        gcm = self.gcm
        recipients = [MockRecipient() for i in xrange(11)]
        recipient_updated_registration_id_pairs = []
        validation_error_codes = []
        retry_after = '1'

        def mock_get_response(request, recipients):
            class MockHTTPResponse:
                def info(self):
                    return self

                def getheader(self, name):
                    return retry_after

            return (
                {
                    'multicast_id': 1000,
                    'success': 2,
                    'failure': 9,
                    'canonical_ids': 2,
                    'results': [
                        {'message_id': '1:1', 'registration_id': '1'},
                        {'message_id': '1:2', 'registration_id': '2'},
                        {'error': 'InvalidRegistration'},
                        {'error': 'NotRegistered'},
                        {'error': 'MismatchSenderId'},
                        {'error': 'InvalidPackageName'},
                        {'error': 'Unavailable'},
                        {'error': 'InternalServerError'},
                        {'error': 'MessageTooBig'},
                        {'error': 'InvalidDataKey'},
                        {'error': 'InvalidTtl'}]},
                MockHTTPResponse())
        gcm._get_response = mock_get_response

        def mock_handle_received_updated_recipient_registration_id(
                recipient, registration_id):
            recipient_updated_registration_id_pairs.append(
                (recipient, registration_id))
        gcm.handle_received_updated_recipient_registration_id = (
            mock_handle_received_updated_recipient_registration_id)

        def mock_mark_recipient_invalid_registration_id(recipient):
            self.assertEqual(recipient, recipients[2])
        gcm.mark_recipient_invalid_registration_id = (
            mock_mark_recipient_invalid_registration_id)

        def mock_mark_recipient_unregistered(recipient):
            self.assertEqual(recipient, recipients[3])
        gcm.mark_recipient_unregistered = (
            mock_mark_recipient_unregistered)

        def mock_log_mismatch(what, mismatched):
            if what == 'sender_id':
                self.assertEqual(mismatched, [recipients[4]])
            elif what == 'package_names':
                self.assertEqual(mismatched, [recipients[5]])
            else:
                self.assertFalse(True)
        gcm.log_mismatch = mock_log_mismatch

        def mock_log_validation_error_result(error_code):
            validation_error_codes.append(error_code)
        gcm.log_validation_error_result = mock_log_validation_error_result

        try:
            gcm.multicast(None, recipients)
            self.assertFalse(True)
        except gcm.ShouldRetry as e:
            self.assertEqual(recipient_updated_registration_id_pairs,
                             [(recipients[0], '1'), (recipients[1], '2')])
            expected_validation_error_codes = (
                list(GcmProxy.RESPONSE_RESULT_VALIDATION_ERRORS))
            expected_validation_error_codes.remove('MissingRegistration')
            self.assertEqual(validation_error_codes,
                             expected_validation_error_codes)
            self.assertEqual(e.recipients, recipients[6:8])
            self.assertEqual(e.retry_kwargs['countdown'], 1)

        recipient_updated_registration_id_pairs = []
        validation_error_codes = []
        retry_after = 'Fri, 31 Dec 1999 23:59:59 GMT'

        try:
            gcm.multicast(None, recipients)
            self.assertFalse(True)
        except gcm.ShouldRetry as e:
            self.assertEqual(recipient_updated_registration_id_pairs,
                             [(recipients[0], '1'), (recipients[1], '2')])
            expected_validation_error_codes = (
                list(GcmProxy.RESPONSE_RESULT_VALIDATION_ERRORS))
            expected_validation_error_codes.remove('MissingRegistration')
            self.assertEqual(validation_error_codes,
                             expected_validation_error_codes)
            self.assertEqual(e.recipients, recipients[6:8])
            retry_timedelta_after_eta = (
                e.retry_kwargs['eta'] - datetime(1999, 12, 31, 23, 59, 59))
            self.assertLessEqual(retry_timedelta_after_eta.seconds,
                                 GcmProxy.RETRY_RANDOM_SECONDS)
