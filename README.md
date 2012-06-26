django-push-notification
========================

## Before You Start

Read the following tutorial carefully. You should have both `pem` files ready, one for the cert and one for the key.

    http://www.raywenderlich.com/3443/apple-push-notification-services-tutorial-part-12

## Dependencies

1. django
2. celery

## Usage
First, you need to add these constants to your `settings.py`. For example,

```python
INSTALLED_APPS = (
    # ... other existing apps
    'push_notifications',
)

APN_PORT = 2195
APN_HOST = 'gateway.push.apple.com'
APN_PASSPHRASE = 'myapncertpassphrase'
APN_DEFAULT_APP_ID = 'ios-app'
APN_CERT_PATH_TEMPLATE =os.path.join(BASE_PATH, 'certs',
    'ios', 'production', '%s.pem')
```

Store your `cert` and `key` file into the following path:

* certs/ios/production/ios-app-cert.pem
* certs/ios/production/ios-app-key.pem

To ensure your settings is setup correctly, runs these tests:

```bash
python manage.py jtest push_notifications
```

If all tests pass, you are good to go.

Then, you will need to associate an apn `device token` with a user. For example,

```python
# views.py

@require_POST
def add_idevice(request):
  # ...
  idevice = IDevice(user=recipient, token=token, app_id=settings.APN_DEFAULT_APP_ID)
  idevice.save()
```

And, you can send push notification to a specific user as the recipient. For example,

```python
from push_notifications.tasks import IDEVICE_NOTIFICATION_TEMPLATE
from push_notifications.models import IDevice

def send_notification(request):
  message = copy.deepcopy(IDEVICE_NOTIFICATION_TEMPLATE)
  message['aps']['alert']['body'] = 'Hello iPhone User'
  IDevice.objects.notify_ios_app(message, user=recipient)

```

That's it.

## License


```
Copyright (c) 2012, Rover.com
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
