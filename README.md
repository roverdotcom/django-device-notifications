django-device-notifications
========================

## Before You Start

Read the following tutorial carefully. You should have both `pem` files ready, one for the cert and one for the key.

    http://www.raywenderlich.com/3443/apple-push-notification-services-tutorial-part-12

## Dependencies

1. django
2. python-gcm (https://github.com/geeknam/python-gcm)


## Usage
First, you need to add these constants to your `settings.py`. For example,

```python
INSTALLED_APPS = (
    # ... other existing apps
    'device_notifications',
)

APN_PASSPHRASE = 'myapncertpassphrase'
APN_DEFAULT_APP_ID = 'app'
```

Store your `cert` and `key` files into the following path:

* certs/ios/production/app-cert.pem
* certs/ios/production/app-key.pem
* certs/ios/development/app-cert.pem
* certs/ios/development/app-key.pem

To ensure your settings is setup correctly, runs these tests:

```bash
python manage.py test device_notifications
```

If all tests pass, setup is done.

Then, you will need a view to let a iOS app register the `device token` for a user. For example,

```python
# views.py

@require_POST
def add_idevice(request):
  # ...
  # add `development=True` if the iOS app is signed 
  # with a development (aka, non distribution) certificate 
  idevice = IDevice(user=recipient, token=token)
  idevice.save()
```

Each user may have more than one device.

A push notification message must follow a specific format. You can inspect `device_notification/settings.py` for an example.

Here is an example code to send a push notification:

```python
from device_notifications.settings import IDEVICE_NOTIFICATION_TEMPLATE
from device_notifications.models import IDevice

def send_notification(request):
  message = copy.deepcopy(IDEVICE_NOTIFICATION_TEMPLATE)
  message['aps']['alert']['body'] = 'Hello iPhone User'
  IDevice.objects.filter(user=receipient).send_message(message)
```

## License

```
Copyright (c) 2012-2013, Rover.com
All rights reserved.

Redistribution and use in source and binary forms, with or without modification,
are permitted provided that the following conditions are met:

* Redistributions of source code must retain the above copyright notice, this 
  list of conditions and the following disclaimer.
* Redistributions in binary form must reproduce the above copyright notice, 
  this list of conditions and the following disclaimer in the documentation 
  and/or other materials provided with the distribution.
  
THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" 
AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE 
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE 
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE 
FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL 
DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR 
SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER 
CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, 
OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE 
OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
```
