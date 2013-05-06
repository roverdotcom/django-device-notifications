from logging import Logger
from logging import NullHandler


class MockLogger(Logger):
    def __init__(self):
        super(MockLogger, self).__init__('mock')
        self.addHandler(NullHandler())

A_LOGGER = MockLogger()
