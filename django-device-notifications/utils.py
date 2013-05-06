from collections import OrderedDict
from math import isnan
from pprint import pformat

LOGGING_LEVELS = ('debug', 'info', 'warning', 'error', 'critical')

LITERALS_TO_JSON_STRINGS = {None: u'null', True: u'true', False: u'false'}
FLOATS_TO_JSON_STRINGS = {
    isnan: 'NaN',
    float('inf'): 'Infinity',
    float('-inf'): '-Infinity'}

HTTP_DATETIME_FORMAT = '%a, %d %b %Y %H:%M:%S GMT'


class ErrorDict(OrderedDict):
    class ErrorList(list):
        pass

    def add(self, key, value):
        if key in self:
            ErrorList = self.ErrorList
            if not isinstance(self[key], ErrorList):
                error_list = ErrorList()
                error_list.append(self[key])
                self[key] = error_list
            else:
                error_list = self[key]
            error_list.append(value)
        else:
            self[key] = value

    def add_all(self, key, values):
        for value in values:
            self.add(key, value)

    class Error(Exception):
        def __init__(self, error_dict=None, *args, **kwargs):
            super(ErrorDict.Error, self).__init__(*args, **kwargs)
            self.error_dict = error_dict or ErrorDict()

        def __getattr__(self, name):
            return getattr(self.error_dict, name)

        def __getitem__(self, key):
            return self.error_dict[key]

        def __setitem__(self, key, value):
            self.error_dict[key] = value

        def __contains__(self, key):
            return key in self.error_dict

        def __eq__(self, other):
            other_error_dict = getattr(other, 'error_dict', None)
            if other_error_dict:
                return (
                    self.error_dict == other_error_dict
                        and type(self) == type(other))
            return self.error_dict == other

        def __repr__(self):
            # TODO
            return repr(self.error_dict)

        IS_NONE = "must not be None"
        NOT_INSTANCE_FORMAT = "must be an instance of {cls.__name__}"

    def raise_error(self, error_class=Error, **kwargs):
        error_message = "\n" + pformat(self, width=1)

        try:
            e = error_class(self, error_message)
        except TypeError:
            e = error_class(error_message)
            e.error_dict = self

        raise e

    def __eq__(self, other):
        try:
            if len(self) != len(other):
                return False
        except TypeError:
            return False

        for key, value in self.iteritems():
            if not key in other:
                return False
            other_value = other[key]
            if (not value == other_value
                    and not (
                        isinstance(other_value, self.ErrorList)
                            and len(other_value) == 1
                            and value == other_value[0])
                    and not (
                        isinstance(value, self.ErrorList)
                            and len(value) == 1
                            and value[0] == other_value)):
                return False

        return True

    def __repr__(self):
        return dict.__repr__(self)
