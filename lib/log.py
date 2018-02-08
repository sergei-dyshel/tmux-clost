import logging
import sys


_logger = logging.getLogger()


def configure(log_file=None, level=logging.DEBUG):
    if not log_file or log_file == '-' or log_file == 'stdout':
        formatter = logging.Formatter('%(message)s')
        handler = logging.StreamHandler(sys.stderr)
    else:
        formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
        handler = logging.FileHandler(log_file)
    handler.setFormatter(formatter)
    _logger.addHandler(handler)
    _logger.setLevel(level)
    warning('========================================================')


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
    _logger.log(level, full_msg)
