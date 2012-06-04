import json
import struct
import binascii
import copy
from OpenSSL import SSL
from socket import socket

from celery.task import task

from settings import APN_PORT, APN_HOST, APN_PASSPHRASE, APN_CERT_PATH_TEMPLATE


APN_MSG_SIZE_LIMIT = 256

IDEVICE_NOTIFICATION_TEMPLATE = { 
    'aps': { 
        'alert': {
                'action-loc-key': 'Open',
                'body': 'You have received a message'
            }, 'badge': 1
        }
    }

def truncate_string(body, oversize):
    body_len = len(body)
    new_body_len = body_len - oversize - 4
    if new_body_len > 0:
        body = ''.join((body[:new_body_len], '...'))
    else:
        msg = 'The length of message payload "%s" exceeded apn limit.' % body
        raise ValueError(msg)
    
    return body

def pack_message(msg, device_token, allow_truncate=True):
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

def create_apn_connection(key_path, cert_path, passphrase):
    ctx = SSL.Context(SSL.SSLv23_METHOD)
    if passphrase is not None and len(passphrase) > 0:
        ctx.set_passwd_cb(lambda *unused: APN_PASSPHRASE)
    ctx.use_privatekey_file(key_path)
    ctx.use_certificate_file(cert_path)

    c = SSL.Connection(ctx, socket())
    c.connect((APN_HOST, APN_PORT))
    c.setblocking(1)

    return c

def send_message(c, packet):
    c.send(packet)

@task
def notify_idevices(msg, devices, app_id):
    cert_path = APN_CERT_PATH_TEMPLATE % (app_id + '-cert')
    key_path = APN_CERT_PATH_TEMPLATE % (app_id + '-key')
    passphrase = APN_PASSPHRASE

    c = create_apn_connection(key_path, cert_path, passphrase)
    try:
        for i in range(len(devices)):
            device = devices[i]
            mail = pack_message(msg, device)
            send_message(c, mail)
    finally:
        if c is not None:
            c.close()

