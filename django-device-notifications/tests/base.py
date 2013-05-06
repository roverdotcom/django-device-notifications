from datetime import datetime
from datetime import timedelta
from unittest import TestCase

from ..utils import ErrorDict

from ..base import MessagingServiceProxy
from ..base import MessageRequest

from ..test.utils import A_LOGGER


class MockMessageRequest(MessageRequest):
    ERROR_DICT = ErrorDict({'key': 'value'})

    def __init__(self, _raises=None, _raises_error_dict=False,
                 **kwargs):
        super(MockMessageRequest, self).__init__(**kwargs)

        if _raises:
            raise _raises
        if _raises_error_dict:
            self.ERROR_DICT.raise_error(self.InitErrors)


class MockRecipient:
    pass

AN_ACCEPTABLE_RECIPIENT = MockRecipient()
ANOTHER_ACCEPTABLE_RECIPIENT = MockRecipient()


class MockMessagingServiceProxy(MessagingServiceProxy):
    request_class = MockMessageRequest
    recipient_class = MockRecipient


class MessagingServiceProxyInitTests(TestCase):
    def test_with_no_logger(self):
        try:
            MockMessagingServiceProxy(None)
            self.assertFalse(True)
        except MockMessagingServiceProxy.InitErrors as e:
            self.assertEqual(e, {'logger': e.NOT_LOGGER})

    def test_with_dev_mode(self):
        logger = A_LOGGER

        default_dev_mode_proxy = MockMessagingServiceProxy(logger)
        dev_proxy = MockMessagingServiceProxy(logger, True)
        production_proxy = MockMessagingServiceProxy(logger, False)

        self.assertTrue(default_dev_mode_proxy.dev_mode)
        self.assertTrue(dev_proxy.dev_mode)
        self.assertFalse(production_proxy.dev_mode)


class MessagingServiceProxySendRequestTests(TestCase):
    class SEND_KWARGS:
        RECIPIENT = {'recipient': AN_ACCEPTABLE_RECIPIENT}
        RECIPIENTS = {'recipients': [AN_ACCEPTABLE_RECIPIENT,
                                     ANOTHER_ACCEPTABLE_RECIPIENT]}
        BOTH_RECIPIENTS = dict(RECIPIENT.items() + RECIPIENTS.items())

    def setUp(self):
        self.proxy = MockMessagingServiceProxy(A_LOGGER)

    def test_with_recipient_xnor_recipients(self):
        proxy = self.proxy

        excepted_error_dict = {
           'recipient': proxy.SendMessageErrors.RECIPIENT,
           'recipients': proxy.SendMessageErrors.RECIPIENTS}

        try:
            proxy.send_message()
            self.assertFalse(True)
        except proxy.SendMessageErrors as e:
            self.assertEqual(e, excepted_error_dict)

        try:
            proxy.send_message(**self.SEND_KWARGS.BOTH_RECIPIENTS)
            self.assertFalse(True)
        except proxy.SendMessageErrors as e:
            self.assertEqual(e, excepted_error_dict)

    def try_with_recipient_and_then_with_recipients(
            self, send_kwargs, excepted_error_dict, send_args=[]):
        proxy = self.proxy

        try:
            proxy.send_message(
                *send_args,
                **dict(
                    send_kwargs.items() + self.SEND_KWARGS.RECIPIENT.items()))
            self.assertFalse(True)
        except proxy.SendMessageErrors as e:
            self.assertEqual(e, excepted_error_dict)

        try:
            proxy.send_message(
                *send_args,
                **dict(
                    send_kwargs.items() + self.SEND_KWARGS.RECIPIENTS.items()))
            self.assertFalse(True)
        except proxy.SendMessageErrors as e:
            self.assertEqual(e, excepted_error_dict)

    def test_with_wrong_request(self):
        class WrongMockMessageRequest(MessageRequest):
            pass

        send_kwargs = {'request': WrongMockMessageRequest(logger=A_LOGGER)}
        excepted_error_dict = {
            'request': MessagingServiceProxy.SendMessageErrors.REQUEST}

        self.try_with_recipient_and_then_with_recipients(
            send_kwargs, excepted_error_dict)

    def test_with_request_init_errors(self):
        an_exception = Exception()

        send_kwargs = {'_raises': an_exception}
        excepted_error_dict = {'request': an_exception}

        self.try_with_recipient_and_then_with_recipients(
            send_kwargs, excepted_error_dict)

        send_kwargs = {'_raises_error_dict': True}
        excepted_error_dict = {'request': MockMessageRequest.ERROR_DICT}

        self.try_with_recipient_and_then_with_recipients(
            send_kwargs, excepted_error_dict)

    def test_with_bad_retries(self):
        send_kwargs = {'retries': None}
        excepted_error_dict = {
            'retries': MessagingServiceProxy.SendMessageErrors.CANT_TO_INT}

        self.try_with_recipient_and_then_with_recipients(
            send_kwargs, excepted_error_dict)

    def test_with_unacceptable_recipients(self):
        proxy = self.proxy
        proxy.did_log_not_sent = False

        def mock_log_not_sent(request, reasons_not_sent_by_recipient):
            proxy.did_log_not_sent = True
            self.assertEqual(reasons_not_sent_by_recipient,
                             expected_reasons_not_sent_by_recipient)
        proxy.log_not_sent = mock_log_not_sent

        unacceptable_recipient = object()

        send_kwargs = {'recipient': unacceptable_recipient}
        try:
            proxy.send_message(**send_kwargs)
            self.assertFalse(True)
        except proxy.SendMessageErrors as e:
            self.assertEqual(
                e, {'recipient':
                        e.NOT_INSTANCE_FORMAT.format(
                            cls=proxy.recipient_class)})
        self.assertFalse(proxy.did_log_not_sent)

        acceptable_recipient_1 = AN_ACCEPTABLE_RECIPIENT

        send_kwargs = {'recipient': unacceptable_recipient,
                       'recipients': [acceptable_recipient_1]}
        try:
            proxy.send_message(**send_kwargs)
            self.assertFalse(True)
        except proxy.SendMessageErrors as e:
            self.assertEqual(e, {'recipient':
                                     [e.RECIPIENT,
                                      e.NOT_INSTANCE_FORMAT.format(
                                         cls=proxy.recipient_class)],
                                 'recipients': e.RECIPIENTS})
        self.assertFalse(proxy.did_log_not_sent)

        send_kwargs = {'recipients': [None, unacceptable_recipient]}
        try:
            proxy.send_message(**send_kwargs)
            self.assertFalse(True)
        except proxy.SendMessageErrors as e:
            self.assertEqual(e, {'recipients': {
                                     None: e.IS_NONE,
                                     unacceptable_recipient:
                                         e.NOT_INSTANCE_FORMAT.format(
                                             cls=proxy.recipient_class)}})
        self.assertFalse(proxy.did_log_not_sent)

        def mock_try_cast(request, recipients):
            proxy.did_try_cast = True
        proxy._try_cast = mock_try_cast

        acceptable_recipient_2 = ANOTHER_ACCEPTABLE_RECIPIENT

        expected_reasons_not_sent_by_recipient = {
            None: MessagingServiceProxy.InitErrors.IS_NONE,
            unacceptable_recipient:
                MessagingServiceProxy.InitErrors.NOT_INSTANCE_FORMAT.format(
                    cls=proxy.recipient_class)}
        proxy.send_message(
            recipients=[None, unacceptable_recipient, acceptable_recipient_1,
                        acceptable_recipient_2])
        self.assertTrue(proxy.did_log_not_sent)
        self.assertTrue(proxy.did_try_cast)

    def test_with_single_recipient_in_recipients(self, recipient=None):
        proxy = self.proxy
        proxy.did_log_unicasting_instead = False
        proxy.did_unicast = False

        def mock_log_unicasting_instead(request, recipient):
            proxy.did_log_unicasting_instead = True
        proxy.log_unicasting_single_recipient_instead_of_multicasting = (
            mock_log_unicasting_instead)

        def mock_unicast(request, recipient):
            proxy.did_unicast = True
        proxy.unicast = mock_unicast

        send_kwargs = {'recipients': [AN_ACCEPTABLE_RECIPIENT]}
        proxy.send_message(**send_kwargs)
        self.assertTrue(proxy.did_log_unicasting_instead)
        self.assertTrue(proxy.did_unicast)

    def test_with_max_recipients(self):
        proxy = self.proxy
        proxy.max_recipients = 1
        proxy.did_log_multiple_casts = False
        proxy.try_cast_counter = 0

        def mock_log_multiple_casts(request, recipient):
            proxy.did_log_multiple_casts = True
        proxy.log_multiple_casts = mock_log_multiple_casts

        def mock_try_cast(request, recipients):
            proxy.try_cast_counter += 1
        proxy._try_cast = mock_try_cast

        proxy.send_message(**self.SEND_KWARGS.RECIPIENTS)
        self.assertTrue(proxy.did_log_multiple_casts)
        self.assertEqual(proxy.try_cast_counter, 2)

    def test_retry_cast_logs_ignored_kwargs(self):
        proxy = self.proxy
        proxy.ignored_retry_kwarg_and_why_pairs = []
        proxy.did_retry_try_cast = False

        retries = 3

        def mock_cast(request, recipient_or_recipients):
            raise proxy.ShouldRetry(retries=retries, max_retries=1,
                                    countdown=1,
                                    eta=datetime.now() + timedelta(seconds=10))
        proxy.unicast = mock_cast
        proxy.multicast = mock_cast

        def mock_log_ignoring_retry_kwarg(kwarg_key, for_what):
            proxy.ignored_retry_kwarg_and_why_pairs.append(
                (kwarg_key, for_what))
        proxy.log_ignoring_retry_kwarg = mock_log_ignoring_retry_kwarg

        def mock_try_cast_retry(**kwargs):
            proxy.did_retry_try_cast = True
            self.assertDictContainsSubset(
                {'max_retries': retries, 'countdown': 1}, kwargs)
        proxy._try_unicast.retry = mock_try_cast_retry
        proxy._try_multicast.retry = mock_try_cast_retry

        proxy.send_message(**self.SEND_KWARGS.RECIPIENT)
        self.assertEqual(proxy.ignored_retry_kwarg_and_why_pairs,
                         [('max_retries', 'retries'),
                          ('eta', "kwargs['countdown']")])
        self.assertTrue(proxy.did_retry_try_cast)

        proxy.ignored_retry_kwarg_and_why_pairs = []
        proxy.did_retry_try_cast = False

        proxy.send_message(**self.SEND_KWARGS.RECIPIENTS)
        self.assertEqual(proxy.ignored_retry_kwarg_and_why_pairs,
                         [('max_retries', 'retries'),
                          ('eta', "kwargs['countdown']")])
        self.assertTrue(proxy.did_retry_try_cast)

    def test_retry_cast_with_retries_kwarg(self):
        proxy = self.proxy
        proxy.cast_count = 0
        proxy.changed_retries = None

        def mock_cast(request, recipient):
            proxy.cast_count += 1
            changed_retries = proxy.changed_retries
            proxy.changed_retries = None
            raise proxy.ShouldRetry(retries=changed_retries)
        proxy.unicast = mock_cast
        proxy.multicast = mock_cast

        proxy.send_message(**self.SEND_KWARGS.RECIPIENT)
        self.assertEqual(proxy.cast_count, proxy.max_retries + 1)

        proxy.cast_count = 0
        proxy.changed_retries = 1

        proxy.send_message(**self.SEND_KWARGS.RECIPIENT)
        self.assertEqual(proxy.cast_count, 2)

        proxy.cast_count = 0
        proxy.changed_retries = None

        proxy.send_message(**self.SEND_KWARGS.RECIPIENTS)
        self.assertEqual(proxy.cast_count, proxy.max_retries + 1)

        proxy.cast_count = 0
        proxy.changed_retries = 1

        proxy.send_message(**self.SEND_KWARGS.RECIPIENTS)
        self.assertEqual(proxy.cast_count, 2)

    def test_retry_multicast_with_not_all_recipients(self):
        proxy = self.proxy

        acceptable_recipient_1 = AN_ACCEPTABLE_RECIPIENT
        expected_recipient = acceptable_recipient_1

        retry_recipients = acceptable_recipient_1
        proxy.cast_count = 0

        def mock_multicast_1(request, recipients):
            proxy.cast_count += 1
            raise proxy.ShouldRetry(retry_recipients)
        proxy.multicast = mock_multicast_1

        def mock_unicast(request, recipient):
            self.assertEqual(recipient, expected_recipient)
            proxy.cast_count += 1
        proxy.unicast = mock_unicast

        proxy.send_message(**self.SEND_KWARGS.RECIPIENTS)
        self.assertEqual(proxy.cast_count, 2)

        retry_recipients = [acceptable_recipient_1]
        proxy.cast_count = 0

        proxy.send_message(**self.SEND_KWARGS.RECIPIENTS)
        self.assertEqual(proxy.cast_count, 2)

        proxy.cast_count = 0

        def mock_multicast_2(request, recipients):
            proxy.cast_count += 1
            raise proxy.ShouldRetry(recipients[0:len(recipients) - 1])
        proxy.multicast = mock_multicast_2

        acceptable_recipient_2 = MockRecipient()

        send_recipients = tuple(set([acceptable_recipient_1,
                                     acceptable_recipient_2,
                                     ANOTHER_ACCEPTABLE_RECIPIENT]))
        expected_recipient = send_recipients[0]

        proxy.send_message(**{'recipients': send_recipients})
        self.assertEqual(proxy.cast_count, 3)
