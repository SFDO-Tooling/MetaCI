""" metaci logger """
# TODO:
#   - disable transaction management?

import datetime
import logging
import os

import coloredlogs
from django.utils import timezone

from metaci.cumulusci.exceptions import LoggerException


class LogStream(object):
    """ File-like interface to Django model. """

    def __init__(self, model):
        if not hasattr(model, "log"):
            raise LoggerException('Model does not have "log" attribute.')
        self.model = model
        self.buffer = ""
        self.last_save_time = timezone.now()

    def flush(self, force=True):
        if self.model.log is None:
            self.model.log = u""
        self.model.log += self.buffer
        self.buffer = ""
        now = timezone.now()
        if force or now - self.last_save_time > datetime.timedelta(seconds=1):
            self.model.save()
            self.last_save_time = now

    def write(self, s):
        self.buffer += s


class LogHandler(logging.StreamHandler):
    """ Handle log messages. """

    def __init__(self, model):
        """ Initialize the handler. """
        super(LogHandler, self).__init__()
        self.stream = LogStream(model)


def init_logger(model):
    """ Initialize the logger. """

    logger = logging.getLogger("cumulusci")

    # Remove existing handlers
    for handler in list(logger.handlers):
        handler.stream.flush()
        logger.removeHandler(handler)
    handler = LogHandler(model)

    # Create the custom handler
    formatter = coloredlogs.ColoredFormatter(fmt="%(asctime)s: %(message)s")
    handler.setLevel(logging.DEBUG)
    handler.setFormatter(formatter)

    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)
    logger.propagate = False

    if os.environ.get("LOG_TO_STDERR"):
        handler = logging.StreamHandler()
        handler.setLevel(logging.DEBUG)
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger
