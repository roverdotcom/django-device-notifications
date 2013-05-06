from abc import ABCMeta
from datetime import datetime
from datetime import timedelta
from collections import defaultdict
from copy import copy
from math import isnan
from random import randint
import json
import urllib2

try:
    from django.core.serializers.json import (
        DjangoJSONEncoder as GcmJsonEncoder)
except ImportError:
    from json import JSONEncoder as GcmJsonEncoder

from ..base import MessageRequest
from ..base import MessagingServiceProxy

from ..utils import LITERALS_TO_JSON_STRINGS
from ..utils import FLOATS_TO_JSON_STRINGS
from ..utils import HTTP_DATETIME_FORMAT
from ..utils import ErrorDict


class GcmRecipient:
    __metaclass__ = ABCMeta

    REQUIRED_ATTRS = ['registration_id', 'is_active', 'invalidated']

    @classmethod
    def __subclasshook__(cls, subclass):
        if cls is GcmRecipient:

            if all(
                   any(attr in C.__dict__ for C in subclass.__mro__)
                       for attr in cls.REQUIRED_ATTRS):
                return True
            else:
                return NotImplemented


class GcmRequest(MessageRequest):
    MAX_TTL = 2419200
    MAX_DATA_LENGTH = 4096

    json_encoder_class = GcmJsonEncoder

    def __init__(
            self, data=None, collapse_key=None, delay_while_idle=None,
            time_to_live=None, restricted_package_name=None, *args, **kwargs):
        try:
            super(GcmRequest, self).__init__(*args, **kwargs)
            errors = ErrorDict()
        except MessageRequest.InitErrors as errors:
            pass

        local_dict = locals()
        content = {}

        if collapse_key is not None:
            self._set_value_or_cls_error(local_dict, content, errors,
                                         'collapse_key', basestring)

        if time_to_live is not None:
            self._set_time_to_live_or_error(local_dict, content, errors)

        if delay_while_idle is not None:
            self._set_value_or_cls_error(local_dict, content, errors,
                                         'delay_while_idle', bool)

        if restricted_package_name is not None:
            self._set_value_or_cls_error(local_dict, content, errors,
                                         'restricted_package_name', basestring)

        data = copy(data)

        if data is not None:
            self._set_data_or_errors(local_dict, content, errors)

        self.content = content

        if errors:
            errors.raise_error(self.InitErrors)

    class InitErrors(MessageRequest.InitErrors):
        @property
        def excess_length(self):
            if not 'data' in self:
                return 0

            data_errors = self['data']
            try:
                return data_errors[self.MAX_DATA_LENGTH_KEY]
            except KeyError:
                for error in data_errors:
                    try:
                        return error[self.MAX_DATA_LENGTH_KEY]
                    except KeyError:
                        pass

            return 0

        NOT_INSTANCE_FORMAT = MessageRequest.InitErrors.NOT_INSTANCE_FORMAT
        NOT_STRING = NOT_INSTANCE_FORMAT.format(cls=basestring)
        NOT_DICT = NOT_INSTANCE_FORMAT.format(cls=dict),
        CANT_TO_INT = "must be castable to int"
        OUT_OF_BOUNDS = "value {value} is not between {min} and {max}"
        NO_COLLAPSE_KEY = 'collapse_key must be specified if time_to_live is'
        RESERVED_DATA_KEY = "is a reserved data key"
        RESERVED_GOOGLE_DATA_KEY = (
            "all data keys starting with 'google.' are reserved")
        DATA_VALUE_CANT_TO_JSON_FORMAT = (
            "data value {value} is not JSON serializable")
    InitErrors.MAX_DATA_LENGTH_KEY = (
        "max data length ({max}) exceeded by".format(max=MAX_DATA_LENGTH))

    class TooLongError(InitErrors):
        pass

    def _set_value_or_cls_error(
            self, from_dict, to_dict, error_dict, key, expected_cls):
        value = from_dict[key]
        if not isinstance(value, expected_cls):
            error_dict[key] = (
                self.InitErrors.NOT_INSTANCE_FORMAT.format(
                    cls=expected_cls))
        else:
            to_dict[key] = value

    def _set_time_to_live_or_error(self, from_dict, to_dict, error_dict):
        try:
            time_to_live = int(from_dict['time_to_live'])
            if not 0 <= time_to_live <= self.MAX_TTL:
                error_dict.add('time_to_live',
                               self.InitErrors.OUT_OF_BOUNDS.format(
                                   value=time_to_live, min=0,
                                   max=str(self.MAX_TTL) + " inclusive"))
        except:
            error_dict['time_to_live'] = self.InitErrors.CANT_TO_INT

        if not from_dict['collapse_key']:
            error_dict.add('time_to_live', self.InitErrors.NO_COLLAPSE_KEY)

        if not error_dict['time_to_live']:
            to_dict['time_to_live'] = time_to_live

    def _set_data_or_errors(self, from_dict, to_dict, error_dict):
        data = from_dict['data']
        if not isinstance(data, dict):
            error_dict['data'] = self.InitErrors.NOT_DICT

        else:
            if 'collapse_key' in data:
                self.log_collapse_key_in_data(self, from_dict['collapse_key'])

            data_errors = ErrorDict()

            if 'from' in data:
                data_errors['from'] = self.InitErrors.RESERVED_DATA_KEY

            data_errors.update(
                (key, self.InitErrors.RESERVED_GOOGLE_DATA_KEY)
                    for key in data
                        if isinstance(key, basestring)
                            and key.startswith('google.'))

            data_length = 0

            for key, value in data.items():
                if not isinstance(key, basestring):
                    data_errors.add(key, self.InitErrors.NOT_STRING)
                    data_length = None
                elif not data_errors:
                    data_length += len(unicode(key))

                if not isinstance(value, basestring):
                    if value in LITERALS_TO_JSON_STRINGS:
                        value = LITERALS_TO_JSON_STRINGS[value]
                    elif isinstance(value, float):
                        if value in FLOATS_TO_JSON_STRINGS:
                            value = FLOATS_TO_JSON_STRINGS[value]
                            data[key] = value
                        elif isnan(value):
                            value = FLOATS_TO_JSON_STRINGS[isnan]
                            data[key] = value
                    else:
                        try:
# TODO: Allow different encodings and verify Python won't butcher them.
                            json.dumps(value, cls=self.json_encoder_class)
                            value = unicode(value)
                        except Exception as e:
                            data_errors.add(
                                key,
                                self.InitErrors
                                    .DATA_VALUE_CANT_TO_JSON_FORMAT
                                        .format(value=value))
                            data_length = None

                if data_length is not None:
                    data_length += len(value)

            if data_length is not None:
                excess_length = data_length - self.MAX_DATA_LENGTH
            else:
                excess_length = 0

            if excess_length > 0:
                max_length_error = {
                    self.InitErrors.MAX_DATA_LENGTH_KEY: excess_length}
                if data_errors:
                    error_dict['data'] = max_length_error
                elif not error_dict:
                    error_dict['data'] = max_length_error
                    error_dict.raise_error(self.TooLongError)
                    self.content = to_dict
                else:
                    data_errors = max_length_error

            if data_errors:
                error_dict.add('data', data_errors)
            else:
                to_dict['data'] = data

    def log_collapse_key_in_data(self, collapse_key):
        if collapse_key:
            self.logger.warn(
                self.LOG_FORMAT_STRINGS.WARN_COLLAPSE_KEY_IN_DATA.format(
                    collapse_key=collapse_key))
        else:
            self.logger.info(
                self.LOG_FORMAT_STRINGS.WARN_COLLAPSE_KEY_IN_DATA)

    class LOG_FORMAT_STRINGS:
        WARN_COLLAPSE_KEY_IN_DATA = "will be overwritten with {collapse_key}"
        INFO_COLLAPSE_KEY_IN_DATA = "should not be set in data"


class GcmProxy(MessagingServiceProxy):
    URL = 'https://android.googleapis.com/gcm/send'

    RESPONSE_RESULT_VALIDATION_ERRORS = (
        'MissingRegistration',
        'MessageTooBig',
        'InvalidDataKey',
        'InvalidTtl')

    RETRY_RANDOM_SECONDS = 60

    request_class = GcmRequest
    recipient_class = GcmRecipient

    def __init__(self, api_key, **kwargs):
        try:
            super(GcmProxy, self).__init__(**kwargs)
            errors = ErrorDict()
        except MessagingServiceProxy.InitErrors as errors:
            pass

        if not isinstance(api_key, basestring):
            errors['api_key'] = self.InitErrors.NOT_STRING
        self.api_key = api_key

        if errors:
            errors.raise_error(self.InitErrors)

    class InitErrors(MessagingServiceProxy.InitErrors):
        NOT_STRING = (
            MessagingServiceProxy.InitErrors.NOT_INSTANCE_FORMAT.format(
                cls=basestring))

    def get_reasons_not_to_send(self, request, recipient):
        reasons_not_to_send = (
            super(GcmProxy, self).get_reasons_not_to_send(request, recipient))

        try:
            if recipient.invalidated:
                if hasattr(recipient, 'device_token'):
                    reasons_not_to_send.append(
                        self.InitErrors.INVALID_TOKEN_FORMAT.format(
                            token=recipient.device_token))
                else:
                    reasons_not_to_send.append(
                        self.InitErrors.INVALID_DEVICE_FORMAT.format(
                            token=recipient.device_token))
        except AttributeError:
            pass

        try:
            if not recipient.is_active:
                reasons_not_to_send.append(
                    self.InitErrors.INACTIVE_RECIPIENT)
        except AttributeError:
            pass

        return reasons_not_to_send

    def multicast(self, request, recipients):
        response, http_response = self._get_response(request, recipients)

        recipient_result_pairs = zip(recipients, response['results'])

        if response['canonical_ids']:
            for recipient, result in recipient_result_pairs:
                if 'registration_id' in result:
                    self.handle_received_updated_recipient_registration_id(
                        recipient, result['registration_id'])

        if response['failure']:
            errors = defaultdict(list)

            for recipient, result in recipient_result_pairs:
                if 'error' in result:
                    errors[result['error']].append(recipient)

            for recipient in errors.get('InvalidRegistration', []):
                self.mark_recipient_invalid_registration_id(recipient)
            for recipient in errors.get('NotRegistered', []):
                self.mark_recipient_unregistered(recipient)

            if 'MismatchSenderId' in errors:
                self.log_mismatch('sender_id', errors['MismatchSenderId'])
            if 'InvalidPackageName' in errors:
                self.log_mismatch(
                    'package_names', errors['InvalidPackageName'])

            for validation_error in self.RESPONSE_RESULT_VALIDATION_ERRORS:
                if validation_error in errors:
                    self.log_validation_error_result(validation_error)

            retry_recipients = (
                errors.pop('Unavailable', [])
                    + errors.pop('InternalServerError', []))

            if retry_recipients:
                errors['retry_recipients'] = retry_recipients
                retry_after = http_response.info().getheader('Retry-After')

                if retry_after:
                    try:
                        countdown = int(retry_after)
                        raise self.ShouldRetry(retry_recipients,
                                               self.max_retries,
                                               countdown=countdown)

                    except (TypeError, ValueError):
                        try:
                            eta = datetime.strptime(retry_after,
                                                    HTTP_DATETIME_FORMAT)
                            eta += (
                                timedelta(
                                    seconds=randint(0,
                                                    self.RETRY_RANDOM_SECONDS))
                            )
                            raise self.ShouldRetry(retry_recipients,
                                                   self.max_retries,
                                                   eta=eta)
                        except ValueError:
                            pass

                raise self.ShouldRetry(recipients=retry_recipients)

    def _get_response(self, request, recipients):
        content = request.content.copy()

        if self.dev_mode:
            content['dry_run'] = True

        content['registration_ids'] = [
            self.get_recipient_registration_id(recipient)
                for recipient in recipients]
        message = json.dumps(content, cls=request.json_encoder_class)

        request_headers = {
            'Authorization': 'key= ' + self.api_key,
            'Content-Type': 'application/json'}

        http_request = urllib2.Request(self.URL, message, request_headers)

        try:
            http_response = urllib2.urlopen(http_request)
        except urllib2.HTTPError as e:
            http_status_code = e.code
            if http_status_code == 400:
                raise GcmFailedValidationError(400)
            elif http_status_code == 401:
                raise GcmAuthenticationError(401)
            elif 501 <= http_status_code <= 599:
                raise self.ShouldRetry
            else:
                raise GcmHttpError(http_status_code)
        except urllib2.URLError as e:
            raise self.ShouldRetry

        return json.loads(http_response.read()), http_response

    def get_recipient_registration_id(self, recipient):
        return recipient.registration_id

    def get_recipient_log_repr(self, recipient):
        return (
            self.LOG_FORMAT_STRINGS.GET_RECIPIENT.format(
                registration_id=self.get_recipient_registration_id(recipient)))

    def handle_received_updated_recipient_registration_id(
            self, recipient, update_registration_id):
        self.log_method_not_overriden(
            'handle_received_updated_recipient_registration_id')

    def mark_recipient_invalid_registration_id(self, recipient):
        self.log_method_not_overriden('mark_recipient_invalid_registration_id')

    def mark_recipient_unregistered(self, recipient):
        self.log_method_not_overriden('mark_recipient_unregistered')

    def log_mismatch(self, what, mismatched):
        self.logger.error(
            self.LOG_FORMAT_STRINGS.MISMATCH.format(
                self.get_recipients_log_repr(locals())))

    def log_validation_error_result(self, error_code):
        self.logger.error(
            self.LOG_FORMAT_STRINGS.VALIDATION_ERROR.format(
                self.get_recipients_log_repr(locals())))

    class LOG_FORMAT_STRINGS:
        GET_RECIPIENT = "<registration_id: {registration_id}>"
        MISMATCH = "Recipients {mismatched} expected different {what}."
        VALIDATION_ERROR = "Validation error occurred. Code: {error_code}."


class GcmHttpError(Exception):
    MESSAGE_FORMAT = "HTTP Status Code: {http_status_code}"

    def __init__(self, http_status_code):
        super(GcmHttpError, self).__init__(
            self.MESSAGE_FORMAT.format(http_status_code=http_status_code))


class GcmFailedValidationError(GcmHttpError):
    pass


class GcmAuthenticationError(GcmHttpError):
    pass


class GcmUnavailableError(GcmHttpError):
    pass
