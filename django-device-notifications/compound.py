from collections import defaultdict

from .base import MessageRequest
from .base import MessagingServiceProxy


class CompoundMessageRequest(object):
    def __init__(self, messaging_service_proxies_by_name, *args, **kwargs):
        self.proxies_by_name = messaging_service_proxies_by_name
        self.real_requests_by_proxy_name = {}

        self.args = args
        self.kwargs = kwargs

    def get_real_request(self, messaging_service_proxy_name):
        real_requests_by_proxy_name = self.real_requests_by_proxy_name

        if messaging_service_proxy_name in real_requests_by_proxy_name:
            return real_requests_by_proxy_name[messaging_service_proxy_name]

        else:
            proxy = self.proxies_by_name[messaging_service_proxy_name]

            real_request = proxy.create_request(self.args, self.kwargs)

            try:
                real_request = proxy.create_request(self.args, self.kwargs)
                real_requests_by_proxy_name[messaging_service_proxy_name] = (
                    real_request)
                return real_request
            except BaseException as e:
                self.request_errors[messaging_service_proxy_name] = e

    def __getitem__(self, key):
        return self.get_real_request(key)


class CompoundMessagingServiceProxy(MessagingServiceProxy):
    request_class = CompoundMessageRequest

    def __init__(self, messaging_service_proxies_by_name, **kwargs):
        try:
            super(CompoundMessagingServiceProxy, self).__init__(**kwargs)
            errors = None
        except MessagingServiceProxy.InitErrors as errors:
            pass

        # TODO make sure all are MessagingServiceProxies
        self.proxies_by_name = messaging_service_proxies_by_name

        if errors:
            raise(self.InitErrors)

    def create_request(self, *args, **kwargs):
        return (
            super(CompoundMessagingServiceProxy, self).create_request(
                self.proxies_by_name, *args, **kwargs))

    def get_reasons_not_to_send(self, request, recipient):
        service_name = self.get_recipient_service_name(recipient)

        proxies_by_name = self.proxies_by_name

        if service_name in proxies_by_name:
            proxy = proxies_by_name[service_name]

            return proxy.get_reasons_not_to_send(request[service_name],
                                                 recipient)

        else:
            return [
                self.ERROR_STRINGS.UNKNOWN_SERVICE_FORMAT.format(
                    service_name=service_name)]

    def unicast(self, request, recipient):
        service_name = self.get_recipient_service_name(recipient)
        proxy = self.proxies_by_name[service_name]
        proxy.unicast(request[service_name], recipient)

    def multicast(self, request, recipients):
        recipients_by_service_name = defaultdict(list)
        for recipient in recipients:
            service_recipients = (
                recipients_by_service_name[
                    self.get_recipient_service_name(recipient)])
            service_recipients.append(recipient)

        proxies_by_name = self.proxies_by_name

        for service_name, service_recipients in (
                recipients_by_service_name.iteritems()):
            if service_name in proxies_by_name:
                proxy = proxies_by_name[service_name]
                proxy.multicast(request[service_name], service_recipients)

        service_name = self.get_recipient_service_name(recipient)

    def get_recipient_service_name(self, recipient):
        pass

    class ERROR_STRINGS:
        UNKNOWN_SERVICE_FORMAT = "unknown service named {service_name!r}"
