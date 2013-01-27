import json
import struct
import binascii
import copy
from OpenSSL import SSL
from socket import socket

import ..settings as settings

APN_MSG_SIZE_LIMIT = 256

IDEVICE_NOTIFICATION_TEMPLATE = {
    'aps': {
        'alert': {
                'action-loc-key': 'Open',
                'body': 'You have received a message'
            }, 'badge': 1
        }
    }

def send_message(device, message):
    pass

def _create_apn_connection(host, port, key_path, cert_path, passphrase):
    ctx = SSL.Context(SSL.SSLv23_METHOD)
    if passphrase is not None and len(passphrase) > 0:
        ctx.set_passwd_cb(lambda *unused: passphrase)
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
        clone['aps']['alert']['body'] = \
                truncate_string(msg['aps']['alert']['body'], oversize)
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

def _notify_idevices(msg, devices, app_id, development=False):
    for attr in ('APN_KEY', 'APN_CERTIFICATE', 'APN_PASSPHRASE'):
        if getattr(settings, attr) is None:
            raise ImproperlyConfigured(
                'You must define %s in your settings file.' % (
                    attr,))

    if len(devices) > 0:
        conn = create_apn_connection(
                settings.APN_HOST,
                settings.APN_PORT,
                settings.APN_KEY,
                settings.APN_CERTIFICATE,
                settings.APN_PASSPHRASE)
        try:
            for i in range(len(devices)):
                mail = pack_message(msg, devices[i])
                conn.send(mail)
        finally:
            if conn is not None:
                conn.close()
