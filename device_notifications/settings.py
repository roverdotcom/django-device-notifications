from django.conf import settings

# Default Apple Push Notifications port is 2195.
APN_PORT = getattr(settings, 'APN_PORT', 2195)

# APN_HOST will varies by default on the DEBUG flag.
APN_HOST = getattr(
    settings,
    'APN_HOST',
    'gateway.sandbox.push.apple.com'
        if settings.DEBUG else
            'gateway.push.apple.com')

# These 3 settings must be defined in your application.
# If they aren't defined, you will get an ImproperlyConfigured
# Exception at runtime.
APN_CERTIFICATE = getattr(
    settings,
    'APN_CERTIFICATE',
    None)
APN_KEY = getattr(
    settings,
    'APN_KEY',
    None)
APN_PASSPHRASE = getattr(
    settings,
    'APN_PASSPHRASE',
    None)

APN_DEFAULT_APP_ID = 'iosapp'

APN_CERT_PATH_TEMPLATE = 'certs/ios/%s'

# By default, do not use celery.
# If you would like to use celery, mark this as True.
# To learn more about celery, visit this documentation here:
# http://docs.celeryproject.org/en/latest/index.html
DEVICE_NOTIFICATIONS_USE_CELERY = getattr(
    settings,
    'DEVICE_NOTIFICATIONS_USE_CELERY',
    False)
