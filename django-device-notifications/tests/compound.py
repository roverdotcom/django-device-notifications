from unittest import TestCase

from ..base import MessagingServiceProxy

from ..compound import CompoundMessagingServiceProxy

from ..test.utils import A_LOGGER


class CompoundMessagingServiceProxyTests(TestCase):
    def test(self):
        class MockRequestClass:
            def __init__(self, *args):
                pass

        proxy_1 = MessagingServiceProxy(logger=A_LOGGER)
        proxy_1.request_class = MockRequestClass

        def mock_unicast_1(request, recipient):
            proxy_1.recipient = recipient
        proxy_1.unicast = mock_unicast_1

        proxy_2 = MessagingServiceProxy(logger=A_LOGGER)
        proxy_2.request_class = MockRequestClass

        def mock_unicast_2(request, recipient):
            proxy_2.recipient = recipient
        proxy_2.unicast = mock_unicast_2

        compound_proxy = CompoundMessagingServiceProxy({1: proxy_1,
                                                        2: proxy_2},
                                                       logger=A_LOGGER)

        def mock_get_recipient_service_name(recipient):
            return recipient.service_name
        compound_proxy.get_recipient_service_name = (
            mock_get_recipient_service_name)

        class MockRecipient:
            service_name = 1

            def __init__(self, service_name=service_name):
                self.service_name = service_name

        recipient_1 = MockRecipient()
        recipient_2 = MockRecipient(2)

        compound_proxy.send_message(recipients=(recipient_1, recipient_2))
        self.assertEqual(proxy_1.recipient, recipient_1)
        self.assertEqual(proxy_2.recipient, recipient_2)

        proxy_1.recipient = None
        compound_proxy.send_message(recipient=recipient_1)
        self.assertEqual(proxy_1.recipient, recipient_1)
