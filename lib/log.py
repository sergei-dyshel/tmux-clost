import logging
import sys

_logger = None

def configure(log_file=None):
    global _logger
    _logger = logging.getLogger('__main__')
    formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
    if not log_file or log_file == '-':
        handler = logging.StreamHandler(sys.stderr)
    else:
        handler = logging.FileHandler(log_file)
    _logger.addHandler(handler)
    handler.setFormatter(formatter)
    _logger.addHandler(handler)
    _logger.setLevel(logging.DEBUG)


def debug(msg, *args, **kwargs):
    return _log(logging.DEBUG, msg, *args, **kwargs)

def info(msg, *args, **kwargs):
    return _log(logging.INFO, msg, *args, **kwargs)

def warning(msg, *args, **kwargs):
    return _log(logging.WARNING, msg, *args, **kwargs)

def error(msg, *args, **kwargs):
    return _log(logging.ERROR, msg, *args, **kwargs)


def _log(level, msg, *args, **kwargs):
    full_msg = msg.format(*args, **kwargs) if args or kwargs else msg
    global _logger
    _logger.log(level, full_msg)


