from django.conf import settings
from django.db.models import get_model

# Default Apple Push Notifications port is 2195.
APN_PORT = getattr(settings, 'APN_PORT', 2195)

# APN_HOST to be used depends the client is built with development
# or distribution certificate
APN_HOST = 'gateway.push.apple.com'

APN_DEVELOPMENT_HOST = 'gateway.sandbox.push.apple.com'

# These 3 settings must be defined in your application.
# If they aren't defined, you will get an ImproperlyConfigured
# Exception at runtime.
APN_PASSPHRASE = getattr(settings, 'APN_PASSPHRASE', None)

# The default `app-id`.
# If you only have one app per server, any value will do.
# With multiple apps, the key will be used to locate the correct certificate.
APN_DEFAULT_APP_ID = getattr(settings, 'APN_DEFAULT_APP_ID', 'app')

# The default Key PEM file for production is:
#   `certs/ios/production/app-key.pem
# The default Cert PEM file for production is:
#   `certs/ios/production/app-cert.pem
APN_CERTIFICATE_PATH_TEMPLATE = getattr(
    settings,
    'APN_CERTIFICATE_PATH_TEMPLATE',
    'certs/ios/{path_prefix}/{app_id}{file_suffix}')

APN_PATH_PREFIX = getattr(
    settings, 'APN_PATH_PREFIX', 'production')

APN_DEVELOPMENT_PATH_PREFIX = getattr(
    settings, 'APN_DEVELOPMENT_PATH_PREFIX', 'development')

APN_KEY_FILE_SUFFIX = getattr(
    settings, 'APN_KEY_FILE_SUFFIX', '-key.pem')

APN_CERT_FILE_SUFFIX = getattr(
    settings, 'APN_CERT_FILE_SUFFIX', '-cert.pem')

# TODO: make this generalized / editable
IDEVICE_NOTIFICATION_TEMPLATE = {
    'aps': {
        'alert': {
            'action-loc-key': 'Open',
            'body': 'You have received a message'
        },
        'badge': 1
    }
}


def get_device_model():
    return get_model(*getattr(settings, 'DEVICE_MODEL', ('', '')))

GCM_API_KEY = getattr(settings, 'GCM_API_KEY', None)

GCM_MAX_TRIES = getattr(settings, 'GCM_MAX_TRIES', 10)
