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
