from os import path
from abc import ABCMeta
from collections import defaultdict
import json
import struct
from binascii import unhexlify
from socket import socket

# TODO: Explore getting rid of this dependency.
from OpenSSL import SSL

try:
    from django.core.serializers.json import (
        DjangoJSONEncoder as ApnJsonEncoder)
except ImportError:
    from json import JSONEncoder as ApnJsonEncoder

from ..utils import ErrorDict

from ..base import MessageRequest
from ..base import MessagingServiceProxy

PAYLOAD_APS_PROPERTIES = ['alert', 'badge', 'sound']
PAYLOAD_APS_ALERT_PROPERTIES = [
    'body', 'action-loc-key', 'loc-key', 'loc-args', 'launch-image']

IOS_SYSTEM_SOUND_FORMATS = ['caf', 'aif', 'wav']


class ApnsRecipient:
    __metaclass__ = ABCMeta

    REQUIRED_ATTRS = [
        'app_id', 'device_token', 'is_active', 'invalidated', 'development']

    DEVICE_TOKEN_BINARY_BYTES_LENGTH = 32

    @classmethod
    def __subclasshook__(cls, subclass):
        if cls is ApnsRecipient:

            if all(
                   any(attr in C.__dict__ for C in subclass.__mro__)
                       for attr in cls.REQUIRED_ATTRS):
                return True
            else:
                return NotImplemented


class ApnsRequest(MessageRequest):
    MAX_PAYLOAD_BYTES = 256

    json_encoder_class = ApnJsonEncoder

    def __init__(self, body=None, badge=None, sound=None, payload=None,
                 *args, **kwargs):
        try:
            super(ApnsRequest, self).__init__(*args, **kwargs)
            errors = ErrorDict()
        except MessageRequest.InitErrors as errors:
            pass

        aps = {}

        if payload is not None:
            if not isinstance(payload, dict):
                errors['payload'] = self.InitErrors.NOT_DICT

            else:

                if 'aps' in payload:
                    aps = payload['aps']
                    aps_errors = {}

                    if not isinstance(aps, dict):
                        aps_errors = self.InitErrors.NOT_DICT
                        aps = {}
                    else:
                        if 'alert' in aps:
                            alert = aps['alert']
                            alert_errors = ErrorDict()

                            if isinstance(alert, basestring):
                                pass

                            elif isinstance(alert, dict):
                                if 'body' in alert and body is None:
                                    self._set_basestring_error(
                                        alert, alert_errors, 'body')

                                if 'loc-key' in alert:
                                    self._set_basestring_error(
                                        alert, alert_errors, 'loc-key')

                                if 'action-loc-key' in alert:
                                    self._set_action_loc_key_error(
                                        alert, alert_errors)

                                if 'loc-args' in alert:
                                    self._set_loc_args_error(
                                        alert, alert_errors)
                                    if not 'loc-key' in alert:
                                        alert_errors.add(
                                            'loc-args',
                                            "loc-key must be specified")

                                if 'launch-image' in alert:
                                    self._set_basestring_error(
                                        alert, alert_errors, 'launch-image')

                                for prop in alert:
                                    if not (prop
                                            in PAYLOAD_APS_ALERT_PROPERTIES):
                                        alert_errors[prop] = (
                                            self.InitErrors.ALERT_PROP)

                            else:
                                alert_errors = self.InitErrors.ALERT_TYPE

                            if alert_errors:
                                aps_errors['alert'] = alert_errors

                        if 'badge' in aps and badge is None:
                            self._set_badge_or_error(aps, aps_errors)

                        if 'sound' in aps and sound is None:
                            self._set_sound_error(aps, aps_errors)

                        for prop in aps:
                            if not prop in PAYLOAD_APS_PROPERTIES:
                                alert_errors[prop] = (
                                    self.InitErrors.APS_PROP)

                    if aps_errors:
                        errors['payload'] = {'aps': aps_errors}

                else:
                    payload['aps'] = aps

        else:
            payload = {'aps': aps}

        local_dict = locals()

        if body is not None:
            self._set_basestring_error(local_dict, errors, 'body')
        if badge is not None:
            self._set_badge_or_error(local_dict, errors)
        if sound is not None:
            self._set_sound_error(local_dict, errors)

        if 'alert' in aps and isinstance(aps['alert'], dict):
            body_dict = alert
            body_key = 'body'
        else:
            body_dict = aps
            body_key = 'alert'

        self._set_if_not_None_delete_if_False(body_dict, body_key, body)
        self._set_if_not_None_delete_if_False(aps, 'badge', badge)
        self._set_if_not_None_delete_if_False(aps, 'sound', sound)

        self.payload = payload

        if errors:
            errors.raise_error(self.InitErrors)
        else:
# TODO: Allow different encodings and verify Python won't butcher them.
            payload_bytes = self.encode_payload(payload)
            self.payload_bytes = payload_bytes
            if len(payload_bytes) > self.MAX_PAYLOAD_BYTES:
                errors.raise_error(self.TooLongError)

    def _set_basestring_error(self, from_dict, error_dict, key):
        if not isinstance(from_dict[key], basestring):
            error_dict[key] = self.InitErrors.NOT_STRING

    def _set_action_loc_key_error(self, from_dict, error_dict):
        action_loc_key = from_dict['action-loc-key']
        if (not isinstance(action_loc_key, basestring)
                and action_loc_key is not None):
            error_dict['action-loc-key'] = (
                self.InitErrors.NOT_STRING_OR_NONE)

    def _set_loc_args_error(self, from_dict, error_dict):
        loc_args = from_dict['loc-args']
        if ((not (isinstance(loc_args, list) or isinstance(loc_args, tuple)))
                or (not isinstance(member, basestring)
                        for member in loc_args)):
            error_dict['loc-args'] = (
                self.InitErrors.NOT_STRING_LIST_OR_TUPLE)

    def _set_badge_or_error(self, badge_dict, error_dict):
        try:
            badge_dict['badge'] = int(badge_dict['badge'])
        except:
            error_dict['badge'] = self.InitErrors.CANT_TO_INT

    def _set_sound_error(self, from_dict, error_dict):
        sound = from_dict['sound']
        try:
            extension_position = sound.rfind('.')         # -1 if no extension
            file_format_position = extension_position + 1  # 0 if no extension
            if (file_format_position
                    and sound[file_format_position:]
                        not in IOS_SYSTEM_SOUND_FORMATS):
                error_dict['sound'] = self.InitErrors.WRONG_SOUND_FORMAT
        except AttributeError:
            error_dict['sound'] = self.InitErrors.WRONG_SOUND_FORMAT

    def _set_if_not_None_delete_if_False(self, dictionary, key, value):
        if value is False:
            if key in dictionary:
                del dictionary[key]
        elif value is not None:
            dictionary[key] = value

    def encode_payload(self, payload):
        return json.dumps(payload, cls=self.json_encoder_class)

    class InitErrors(MessageRequest.InitErrors):
        NOT_STRING = "must be an instance of basestring"
        NOT_STRING_OR_NONE = "must be None or an instance of basestring"
        NOT_STRING_LIST_OR_TUPLE = "must be a list or tuple of basestrings"
        NOT_DICT = "must be an instance of dict"
        CANT_TO_INT = "must be castable to int"
        APS_PROP = "invalid ap property"
        ALERT_TYPE = "must be basestring or dict"
        ALERT_PROP = "invalid alert property"
        WRONG_SOUND_FORMAT = (
            "if file format specified, must be one of {formats}".format(
                formats=IOS_SYSTEM_SOUND_FORMATS))

    class TooLongError(InitErrors):
        pass


class ApnsConnectionContextManager(object):
    HOST = 'gateway.push.apple.com'
    DEV_MODE_HOST = 'gateway.sandbox.push.apple.com'

    PORT = 2195

    def __init__(self, dev_mode, cert_path=None, key_path=None, password=None,
                 **kwargs):
        errors = ErrorDict()

        for key in kwargs:
            errors[key] = self.InitErrors.UNKNOWN_KEY

        if key_path is not None:
            if not isinstance(key_path, basestring):
                errors['key_path'] = self.InitErrors.NOT_STRING
            elif not path.isfile(key_path):
                errors['key_path'] = self.InitErrors.NOT_FILE
        else:
            key_path = cert_path

        if cert_path is None:
            errors['cert_path'] = self.InitErrors.NOT_PROVIDED
        elif not isinstance(cert_path, basestring):
            errors['cert_path'] = self.InitErrors.NOT_STRING
        elif not path.isfile(cert_path):
            errors['cert_path'] = self.InitErrors.NOT_FILE

        if password is not None and not isinstance(password, basestring):
            errors['password'] = self.InitErrors.NOT_STRING

        if errors:
            errors.raise_error(self.InitErrors)

        self.init_context(dev_mode, cert_path, key_path, password)

    def init_context(self, dev_mode, cert_path, key_path, password):
        ssl_context = SSL.Context(SSL.SSLv23_METHOD)

        if password:
            ssl_context.set_passwd_cb(lambda *ignore_args: password)

        ssl_context.use_privatekey_file(key_path)
        ssl_context.use_certificate_file(cert_path)

        self.ssl_context = ssl_context

        if dev_mode:
            self.host = self.DEV_MODE_HOST
        else:
            self.host = self.HOST
        self.port = self.PORT

        self.connection = None

    class InitErrors(ErrorDict.Error):
        UNKNOWN_KEY = "unknown key"
        NOT_PROVIDED = "must be provided"
        NOT_STRING = (
            ErrorDict.Error.NOT_INSTANCE_FORMAT.format(cls=basestring))
        NOT_FILE = "must be a file path"

    def __enter__(self):
        connection = self.connection

        if not connection:
            connection = SSL.Connection(self.ssl_context, socket())
            self.connection = connection

        connection.connect((self.host, self.port))
        connection.setblocking(1)

        return connection

    def __exit__(self, exc_type, exc_value, traceback):
        self.connection.close()


class ApnsProxy(MessagingServiceProxy):
    request_class = ApnsRequest
    recipient_class = ApnsRecipient
    connection_context_manager_class = ApnsConnectionContextManager

    def __init__(self, connection_contexts_by_app_id, password=None, **kwargs):
        try:
            super(ApnsProxy, self).__init__(**kwargs)
            errors = ErrorDict()
        except MessagingServiceProxy.InitErrors as errors:
            pass

        if not isinstance(connection_contexts_by_app_id, dict):
            errors['connection_contexts_by_app_id'] = self.InitErrors.NOT_DICT
        else:
            connection_contexts_by_app_id = (
                connection_contexts_by_app_id.copy())

            connection_contexts_by_app_id_errors = ErrorDict()

            for app_id, connection_context in (
                    connection_contexts_by_app_id.iteritems()):
                if not isinstance(app_id, basestring):
                    connection_contexts_by_app_id_errors[app_id] = (
                        self.InitErrors.NOT_STRING)

                connection_context_manager_class = (
                    self.connection_context_manager_class)

                if isinstance(connection_context,
                              connection_context_manager_class):
                    pass

                elif isinstance(connection_context, dict):
                    connection_context = connection_context.copy()

                    if not 'password' in connection_context:
                        connection_context['password'] = password

                    try:
                        connection_contexts_by_app_id[app_id] = (
                            connection_context_manager_class(
                                self.dev_mode, **connection_context))
                    except BaseException as e:
                        connection_contexts_by_app_id_errors.add(app_id, e)
                else:
                    connection_contexts_by_app_id_errors.add(
                        app_id,
                        self.InitErrors.NOT_CONNECTION_CONTEXT_FORMAT.format(
                            cls=connection_context_manager_class))

            if connection_contexts_by_app_id_errors:
                errors['connection_contexts_by_app_id'] = (
                    connection_contexts_by_app_id_errors)
            else:
                self.connection_contexts_by_app_id = (
                    connection_contexts_by_app_id)

        if not (password is None or isinstance(password, basestring)):
            errors['password'] = self.InitErrors.NOT_STRING

        if errors:
            errors.raise_error(self.InitErrors)

    def get_reasons_not_to_send(self, request, recipient):
        reasons_not_to_send = (
            super(ApnsProxy, self).get_reasons_not_to_send(request, recipient))

        try:
            recipient_dev_mode = recipient.development
            if recipient_dev_mode != self.dev_mode:
                reasons_not_to_send.append(
                    self.InitErrors.WRONG_MODE_FORMAT.format(
                        recipient_mode=(
                            "dev" if recipient_dev_mode else "production")))
        except AttributeError:
            pass

        try:
            app_id = recipient.app_id
            if not app_id in self.connection_contexts_by_app_id:
                reasons_not_to_send.append(
                    self.InitErrors.UNKNOWN_APP_ID_FORMAT.format(
                        app_id=app_id))
        except AttributeError:
            pass

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

    class InitErrors(MessagingServiceProxy.InitErrors):
        NOT_INSTANCE_FORMAT = (
            MessagingServiceProxy.InitErrors.NOT_INSTANCE_FORMAT)
        NOT_STRING = NOT_INSTANCE_FORMAT.format(cls=basestring)
        NOT_DICT = NOT_INSTANCE_FORMAT.format(cls=dict)
        NOT_CONNECTION_CONTEXT_FORMAT = (
            "must either be an instance of {cls.__name__} or a dict of keyword"
            " args to instantiate one")
        WRONG_MODE_FORMAT = "{recipient_mode} token"
        UNKNOWN_APP_ID_FORMAT = (
            "no credentials for sending to app with id {app_id!r}")
        INVALID_TOKEN_FORMAT = "invalid device token {token}"
        INVALID_DEVICE_FORMAT = "invalid device"
        INACTIVE_RECIPIENT = "not active"

    def unicast(self, request, recipient):
        with self.connection_contexts_by_app_id[recipient.app_id] as (
                connection):
            try:
                connection.send(self.get_packed_bytes(request, recipient))
            except SSL.ZeroReturnError:
                raise self.ShouldRetry

    def multicast(self, request, recipients):
        recipients_by_app_id = defaultdict(list)
        for recipient in recipients:
            recipients_by_app_id[recipient.app_id].append(recipient)

        for app_id, app_recipients in recipients_by_app_id.iteritems():
            with self.connection_contexts_by_app_id[app_id] as (
                    connection):
                for recipient in app_recipients:
                    try:
                        connection.send(self.get_packed_bytes(request,
                                                              recipient))
                        recipients.remove(recipient)
                    except SSL.ZeroReturnError:
                        raise self.ShouldRetry(recipients)

    def get_packed_bytes(self, request, recipient):
        payload_bytes = request.payload_bytes
        device_token_binary_bytes_length = (
            ApnsRecipient.DEVICE_TOKEN_BINARY_BYTES_LENGTH)
        payload_length = len(payload_bytes)
        struct_format = (
                "!" # network byte order (big-endian)
                "B" # 1 byte command
# TODO: Use new APNS message format
                # "{enhanced_fields}"
                "H" # 2 byte token length
                "{token_length}s" # token
                "H" # 2 byte payload length
                "{payload_length}s" # payload
            ).format(token_length=device_token_binary_bytes_length/2,
                     payload_length=payload_length)
        command = 0
        return (
            struct.pack(
                struct_format, command, device_token_binary_bytes_length,
                self.get_recipient_binary_device_token(recipient),
                payload_length, payload_bytes))

    def get_recipient_binary_device_token(self, recipient):
        return unhexlify(recipient.device_token)
