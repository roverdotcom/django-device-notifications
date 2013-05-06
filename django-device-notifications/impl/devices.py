from abc import ABCMeta

from ..base import MessageRequest

from ..compound import CompoundMessageRequest
from ..compound import CompoundMessagingServiceProxy

from .apns import ApnsProxy
from .apns import ApnsRequest
from .gcm import GcmProxy
from .gcm import GcmRequest


DEVICE_TYPE_ANDROID = 'android'
DEVICE_TYPE_IOS = 'ios'


class SimpleNotificationRequest(CompoundMessageRequest):
    truncated_notification_endings = "..."

    def __init__(self, notification, *args, **kwargs):
        super(SimpleNotificationRequest).__init__(*args, **kwargs)
        self.notification = notification

    def get_real_request(self, messaging_service_proxy_name):
        super(SimpleNotificationRequest, self).get_real_request(
            messaging_service_proxy_name)
        try:
            if messaging_service_proxy_name in self.request_errors:
                proxy = self.proxies_by_name[messaging_service_proxy_name]
                args = list(self.args)
                kwargs = self.kwargs.copy()
                raise self.request_errors[messaging_service_proxy_name]
        except GcmRequest.TooLongError as e:
            if not 'data' in kwargs:
                
                self.request_errors[messaging_service_proxy_name] = e
                return

            # TODO constant n and ending
            notification = kwargs['data']['n']
            truncated_ending = self.truncated_notification_ending
            length_to_truncate = e.excess_length + len(truncated_ending)
            new_length = len(notification) - length_to_truncate

            kwargs['data']['n'] = (
                notification[0:new_length] + truncated_ending)

            try:
                real_request = proxy.create_request(self.args, kwargs)
                self.real_requests_by_proxy_name[DEVICE_TYPE_ANDROID] = (
                    real_request)
                return real_request
            except BaseException as e:
                self.request_errors[messaging_service_proxy_name] = e

        except ApnsRequest.TooLongError as e:

                # TODO truncate


class Device:
    __metaclass__ = ABCMeta

    @classmethod
    def __subclasshook__(cls, subclass):
        if cls is Device:
            if any('device_type' in C.__dict__ for C in subclass.__mro__):
                return True
            else:
                return NotImplemented


class SimpleDeviceNotificationServiceProxy(CompoundMessagingServiceProxy):
    request_class = SimpleNotificationRequest
    recipient_class = Device

    def __init__(self, apns_kwargs, gcm_kwargs, **kwargs):
        apns_kwargs = apns_kwargs.copy()
        apns_kwargs.update(kwargs)
        gcm_kwargs = gcm_kwargs.copy()
        gcm_kwargs.update(kwargs)
        super(SimpleDeviceNotificationServiceProxy, self).__init__(
            {DEVICE_TYPE_IOS: ApnsProxy(**apns_kwargs),
             DEVICE_TYPE_ANDROID: GcmProxy(**gcm_kwargs)},
            **kwargs)

    def get_recipient_service_name(self, recipient):
        return recipient.device_type
