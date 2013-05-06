from collections import Iterable
from copy import copy
from logging import Logger

try:
    from django import settings
    from sys import argv
    DEV_MODE_DEFAULT = settings.DEBUG or 'test' in ' '.join(argv[1:len(argv)])
except ImportError:
    DEV_MODE_DEFAULT = True

from .task import task
from .task import get_task_logger

from .utils import ErrorDict


class MessageRequest(object):
    def __init__(self, **kwargs):
        errors = ErrorDict()

        logger = kwargs.pop('logger', None)
        if isinstance(logger, Logger):
            self.logger = logger
        else:
            errors['logger'] = self.InitErrors.NOT_LOGGER

        if errors:
            errors.raise_error(self.InitErrors)

    class InitErrors(ErrorDict.Error):
        NOT_LOGGER = ErrorDict.Error.NOT_INSTANCE_FORMAT.format(cls=Logger)


class MessagingServiceProxy(object):
    max_recipients = None
    max_retries = 4

    request_class = None
    recipient_class = None

    def __init__(self, logger=None, dev_mode=DEV_MODE_DEFAULT):
        errors = ErrorDict()

        self.dev_mode = dev_mode

        logger = logger or get_task_logger(self.__class__.__name__)
        if isinstance(logger, Logger):
            self.logger = logger
        else:
            errors['logger'] = self.InitErrors.NOT_LOGGER

        self.send_message = (
            task(max_retries=0, ignore_result=True)(self.send_message))
        self._try_unicast = task(ignore_result=True)(self._try_unicast)
        self._try_multicast = task(ignore_result=True)(self._try_multicast)

        if errors:
            errors.raise_error(self.InitErrors)

    class InitErrors(ErrorDict.Error):
        NOT_LOGGER = ErrorDict.Error.NOT_INSTANCE_FORMAT.format(cls=Logger)

    def send_message(self, *args, **kwargs):
        args = copy(args)
        kwargs = copy(kwargs)

        errors = ErrorDict()

        kwargs['logger'] = self.logger

        request = kwargs.pop('request', None)

        recipient = kwargs.pop('recipient', None)
        bool_recipient = bool(recipient)

        try:
            intended_recipients = kwargs.pop('recipients', [])
            if isinstance(intended_recipients, basestring):
                intended_recipients = (intended_recipients,)
            intended_recipients = set(intended_recipients)
        except BaseException as e:
            errors['recipients'] = e.message
            intended_recipients = []
            bool_recipients = True
        else:
            bool_recipients = bool(intended_recipients)

        if bool_recipient == bool_recipients:
            errors['recipient'] = self.SendMessageErrors.RECIPIENT
            errors.add('recipients', self.SendMessageErrors.RECIPIENTS)

        retries = kwargs.pop('retries', self.max_retries)
        try:
            self.retries = int(retries)
        except:
            errors['retries'] = self.SendMessageErrors.CANT_TO_INT

        if request is None:
            try:
                request = self.create_request(*args, **kwargs)
            except BaseException as e:
                errors['request'] = e
        else:
            if not self.accepts_request(request):
                errors['request'] = self.SendMessageErrors.REQUEST

        if recipient is not None:
            # Single recipient.
            errors.add_all('recipient',
                           self.get_reasons_not_to_send(request, recipient))

            if not errors:
                self._try_unicast.delay(self, request, recipient)
                return

        if intended_recipients:
            # Multiple recipients.
            reasons_not_to_send_by_recipient = ErrorDict()
            recipients = []
            for recipient in intended_recipients:
                reasons_not_to_send = (
                    self.get_reasons_not_to_send(request, recipient))
                if reasons_not_to_send:
                    reasons_not_to_send_by_recipient.add_all(
                        recipient, reasons_not_to_send)
                else:
                    recipients.append(recipient)

            failed = errors or not recipients

            if reasons_not_to_send_by_recipient:
                if failed:
                    errors.add('recipients', reasons_not_to_send_by_recipient)
                else:
                    self.log_not_sent(request,
                                      reasons_not_to_send_by_recipient)

            if not failed:
                num_recipients = len(recipients)
                max_recipients = self.max_recipients

                i = 0

                # Send multiple requests if maximum recipients exceeded.
                if max_recipients and num_recipients > max_recipients:
                    self.log_multiple_casts(request, recipients)
                    for j in xrange(max_recipients, num_recipients,
                                    max_recipients):
                        self._try_cast(request, recipients[i:j])
                        i = j

                j = num_recipients
                self._try_cast(request, recipients[i:j])

        if errors:
            errors.raise_error(self.SendMessageErrors,
                               method=self.send_message)

    def accepts_request(self, request):
        request_class = self.request_class
        return not request_class or isinstance(request, request_class)

    def create_request(self, *args, **kwargs):
        return self.request_class(*args, **kwargs)

    def get_reasons_not_to_send(self, request, recipient):
        if recipient is None:
            return [self.SendMessageErrors.IS_NONE]
        elif (self.recipient_class
                and not isinstance(recipient, self.recipient_class)):
            return [
                self.SendMessageErrors.NOT_INSTANCE_FORMAT.format(
                    cls=self.recipient_class)]
        else:
            return []

    class SendMessageErrors(ErrorDict.Error):
        CANT_TO_INT = "must be castable to int"
        RECIPIENT = "must (only) be provided if recipients is not"
        RECIPIENTS = "must (only) be provided if recipient is not"
        REQUEST = "invalid request"

    def _try_cast(self, request, recipients, retry_kwargs={}):
        if (len(recipients) == 1):
            recipient = recipients[0]

            if self.should_unicast_single_recipient(request, recipient):
                self.log_unicasting_single_recipient_instead_of_multicasting(
                    request, recipient)
                self._try_unicast.apply_async(
                    (self, request, recipient), **retry_kwargs)
        else:
            self._try_multicast.apply_async(
                (self, request, recipients), **retry_kwargs)

    def should_unicast_single_recipient(self, request, recipient):
        return self.unicast != MessagingServiceProxy.unicast

    def _try_unicast(self, request, recipient):
        try:
            self.unicast(request, recipient)
        except MessagingServiceProxy.ShouldRetry as e:
            self._retry(self._try_unicast, request, e, recipient=recipient)

    def _try_multicast(self, request, recipients):
        try:
            self.multicast(request, recipients)

        except MessagingServiceProxy.ShouldRetry as e:
            if e.recipients:
                intended_retry_recipients = e.recipients

                if intended_retry_recipients is not None:
                    if (not isinstance(intended_retry_recipients, Iterable)
                            or isinstance(intended_retry_recipients,
                                          basestring)):
                        intended_retry_recipients = (
                            intended_retry_recipients,)
                    intended_retry_recipients = set(intended_retry_recipients)

                    retry_recipients = (
                        intended_retry_recipients.intersection(
                            tuple(recipients)))

                    if not intended_retry_recipients == retry_recipients:
                        self.log_shouldnt_retry_all_recipients(
                            request,
                            [recipient
                                for recipient in intended_retry_recipients
                                if not recipient in retry_recipients],
                            e)

                    if retry_recipients != recipients:
                        self._try_cast(request, tuple(retry_recipients),
                                       e.retry_kwargs)
                        return

            self._retry(self._try_multicast, request, e, recipients=recipients)

    def unicast(self, request, recipient):
        if self.multicast == MessagingServiceProxy.multicast:
            self.log_method_not_overriden("unicast or .multicast")
            return

        self.multicast(request, [recipient])

    def multicast(self, request, recipients):
        if self.unicast == MessagingServiceProxy.unicast:
            self.log_method_not_overriden("multicast or .unicast")
            return

        retry_recipients = []

        for recipient in recipients:
            try:
                self.unicast(request, recipient)
            except self.ShouldRetry as e:
                retry_recipients.extend(e.recipients)

        if retry_recipients:
            raise self.ShouldRetry(retry_recipients)

    class ShouldRetry(Exception):
        def __init__(self, recipients=None, retries=None, **kwargs):
            self.recipients = recipients
            self.retries = retries
            self.retry_kwargs = kwargs

    def _retry(self, which_task, request, e, **recipent_or_recipients_kwargs):
        times_retried = which_task.request.retries
        retries_left = e.retries

        retry_kwargs = e.retry_kwargs

        if retries_left:
            if 'max_retries' in retry_kwargs:
                self.log_ignoring_retry_kwarg('max_retries', 'retries')

            max_retries = times_retried + retries_left
            retry_kwargs['max_retries'] = max_retries
            self.retries = max_retries

        else:
            retries_left = self.retries - times_retried

        if 'countdown' in retry_kwargs:
            if 'eta' in retry_kwargs:
                self.log_ignoring_retry_kwarg('eta', "kwargs['countdown']")
        elif not 'eta' in retry_kwargs:
            retry_kwargs['countdown'] = (
                self.get_retry_countdown(request, retries_left,
                                         **recipent_or_recipients_kwargs))

        if retries_left > 0:
            which_task.retry(**retry_kwargs)

    def get_retry_countdown(
            self, request, retries_left, recipient=None, recipients=None):
        return (2 ** (self.max_retries - retries_left) * 60 * 5)

    def get_recipient_log_repr(self, recipient):
        self.log_method_not_overriden('get_recipient_log_repr')
        return repr(recipient)

    def get_recipients_log_repr(self, recipients):
        if (self.get_recipient_log_repr
                == MessagingServiceProxy.get_recipient_log_repr):
            self.log_method_not_overriden('get_recipient_log_repr')
            return (
                "[" + ", ".join(repr(recipient) for recipient in recipients)
                    + "] ()")
        else:
            return (
                "[" + ", ".join(
                        (self.get_recipient_log_repr(recipient)
                            for recipient in recipients))
                    + "]")

    def log_not_sent(self, request, reasons_not_sent_by_recipient):
        reasons_not_sent_by_recipient = (
            ErrorDict(reasons_not_sent_by_recipient))
        self.logger.warn(
            self.LOG_FORMAT_STRINGS.NOT_SENT.format(
                request=request,
                reasons_not_sent_by_recipient=reasons_not_sent_by_recipient))

    def log_multiple_casts(self, request, recipient):
        self.logger.info(
            self.LOG_FORMAT_STRINGS.MULTIPLE_CASTS.format(**locals()))

    def log_unicasting_single_recipient_instead_of_multicasting(
            self, request, recipient):
        self.logger.info(
            self.LOG_FORMAT_STRINGS
                .UNICASTING_SINGLE_RECIPIENT_INSTEAD_OF_MULTICASTING
                    .format(**locals()))

    def log_shouldnt_retry_all_recipients(
            self, request, not_retry_recipients, e):
        self.logger.warn(
            self.LOG_FORMAT_STRINGS.SHOULDNT_RETRY_ALL_RECIPIENTS
                .format(**locals()))

    def log_ignoring_retry_kwarg(self, kwarg_key, for_what):
        self.logger.warn(
            self.LOG_FORMAT_STRINGS.IGNORING_RETRY_KWARG.format(**locals()))

    def log_method_not_overriden(self, method_name):
        self.logger.error(
            self.LOG_FORMAT_STRINGS.METHOD_NOT_OVERRIDEN
                .format(class_name=self.__class__, method_name=method_name))

    class LOG_FORMAT_STRINGS:
        NOT_SENT = ("Not sending messages to the following recipients:"
                    "\n{reasons_not_sent_by_recipient!r}")
        MULTIPLE_CASTS = "Splitting into multiple message request submissions."
        UNICASTING_SINGLE_RECIPIENT_INSTEAD_OF_MULTICASTING = (
            "Sending message to {recipient} as unicast instead of multicast.")
        SHOULDNT_RETRY_ALL_RECIPIENTS = ("{not_retry_recipients} are not among"
                                         " the original recipients. Ignoring.")
        METHOD_NOT_OVERRIDEN = "Please override {class_name}.{method_name}."
