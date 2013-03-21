import json
import struct
import binascii
import copy
import os

from OpenSSL import SSL
from socket import socket

from django.core.exceptions import ImproperlyConfigured


import .settings as settings
from .models as AbstractBaseDevice


APN_MSG_SIZE_LIMIT = 256


def send_message(devices, message):
    if isinstance(devices, AbstractBaseDevice):
        devices = [devices]
    _notify_idevices(
        message,
        [device.token for device in devices],
        development=devices[0].development)


def _create_apn_connection(host, port, key_path, cert_path, passphrase):
    ctx = SSL.Context(SSL.SSLv23_METHOD)
    if passphrase is not None and len(passphrase) > 0:
        ctx.set_passwd_cb(lambda *unused: passphrase)

    if not os.path.isfile(key_path):
        msg = 'The key file "%s" is not valid.' % key_path
        raise ValueError(msg)

    if not os.path.isfile(cert_path):
        msg = 'The cert file "%s" is not valid.' % cert_path
        raise ValueError(msg)

    ctx.use_privatekey_file(key_path)
    ctx.use_certificate_file(cert_path)

    c = SSL.Connection(ctx, socket())
    c.connect((host, port))
    c.setblocking(1)

    return c


def _pack_message(msg, device_token, allow_truncate=True):
    payload = json.dumps(msg)

    oversize = len(payload) - APN_MSG_SIZE_LIMIT
    if oversize > 0:
        if not allow_truncate:
            msg = 'The length of message "%s" exceeded apn limit.' % payload
            raise ValueError(msg)

        # truncate body to fit the limit, if possible
        clone = copy.deepcopy(msg)
        clone['aps']['alert']['body'] = _truncate_string(
            msg['aps']['alert']['body'],
            oversize)
        payload = json.dumps(clone)

    header = "!cH32sH%ds" % len(payload)
    command = '\x00'
    mail = struct.pack(header, command, 32,
                      binascii.unhexlify(device_token), len(payload), payload)
    return mail


def _truncate_string(body, oversize):
    body_len = len(body)
    new_body_len = body_len - oversize - 4
    if new_body_len > 0:
        body = ''.join((body[:new_body_len], '...'))
    else:
        msg = 'The length of message payload "%s" exceeded apn limit.' % body
        raise ValueError(msg)

    return body


def _concat_path(
        app_id=settings.APN_DEFAULT_APP_ID,
        key=False,
        development=False):
    if key:
        file_suffix = settings.APN_KEY_FILE_SUFFIX
    else:
        file_suffix = settings.APN_CERT_FILE_SUFFIX

    if development:
        path_prefix = settings.APN_DEVELOPMENT_PATH_PREFIX
    else:
        path_prefix = settings.APN_PATH_PREFIX

    path = settings.APN_CERTIFICATE_PATH_TEMPLATE.format(
        path_prefix=path_prefix, app_id=app_id, file_suffix=file_suffix)

    return path


def _notify_idevices(
        msg,
        devices,
        app_id=settings.APN_DEFAULT_APP_ID,
        development=False):
    if getattr(settings, 'APN_PASSPHRASE') is None:
        raise ImproperlyConfigured(
            'Expect "%s" in your settings file.' % ('APN_PASSPHRASE'))

    key_path = _concat_path(key=True, development=development)
    cert_path = _concat_path(key=False, development=development)
    host = settings.APN_HOST

    if len(devices) > 0:
        conn = _create_apn_connection(
                host,
                settings.APN_PORT,
                key_path,
                cert_path,
                settings.APN_PASSPHRASE)
        try:
            for i in range(len(devices)):
                mail = _pack_message(msg, devices[i])
                conn.send(mail)
        finally:
            if conn is not None:
                conn.close()
