import tmux
import sys
import os.path
import os
from argparse import Namespace

from . import environment, log, config

class ClostError(Exception):
    def __init__(self, msg, *args, **kwargs):
        if args or kwargs:
            msg = msg.format(*args, **kwargs)
        super(ClostError, self).__init__(msg)

def display_exception(exc_info):
    import traceback
    exc_type, exc_val, exc_tb = exc_info
    for line in traceback.format_exception_only(exc_type, exc_val):
        log.error(line.rstrip())
    for line in traceback.format_tb(exc_tb):
        log.debug(line.rstrip())
    exc_msg = (str(exc_val) if issubclass(exc_type, ClostError) else
               'Exception raised  - {}: {}'.format(exc_type.__name__, exc_val))
    display_status(exc_msg)

class handle_exceptions(object):
    def __init__(self, func=None):
        self._func = func
    def __enter__(self):
        pass
    def __exit__(self, *exc_info):
        exc_type = exc_info[0]
        if exc_type is None or not issubclass(exc_type, Exception):
            return True
        if sys.stdin.isatty():
            return False
        display_exception(exc_info)
        if self._func is not None:
            self._func()
        log.debug('Exiting')
        sys.exit()

def display_status(msg, *args, **kwargs):
    if args or kwargs:
        msg = msg.format(*args, **kwargs)
    tmux.display_message('Clost: ' + msg)


