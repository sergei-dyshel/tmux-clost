import tmux
import sys
import logging
import os.path
import re
import os

reload(sys)
sys.setdefaultencoding('utf8')

try:
    import re2 as re
except ImportError:
    import re

ERROR_TIMEOUT = 5000
_workdir = None
_logger = None

def _init_logger():
    logger = logging.getLogger('__main__')
    formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
    if sys.stdin.isatty():
        handler = logging.StreamHandler(sys.stderr)
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    log_path = '/tmp/tmux-clost.log'
    handler = logging.FileHandler(log_path)
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)
    return logger

def _log(level, msg, *args, **kwargs):
    full_msg = msg.format(*args, **kwargs) if args or kwargs else msg
    global _logger
    if _logger is None:
        _logger = _init_logger()
    _logger.log(level, full_msg)

def log_debug(msg, *args, **kwargs):
    return _log(logging.DEBUG, msg, *args, **kwargs)

def log_info(msg, *args, **kwargs):
    return _log(logging.INFO, msg, *args, **kwargs)

def log_warning(msg, *args, **kwargs):
    return _log(logging.WARNING, msg, *args, **kwargs)

def log_error(msg, *args, **kwargs):
    return _log(logging.ERROR, msg, *args, **kwargs)

def wrap_main(main):
    try:
        main(sys.argv)
    except BaseException as exc:
        if sys.stdin.isatty():
            # executed by user
            raise
        else:
            # executed by tmux
            import traceback
            log_error(traceback.format_exc())
            import inspect
            script = os.path.basename(inspect.getsourcefile(main))
            msg = 'Clost: {} failed with {}: {}'.format(
                script, exc.__class__.__name__, exc)
            tmux.display_message(msg, ERROR_TIMEOUT)

def get_config_var(opt_name, default=None, mandatory=False):
    full_opt_name = '@clost_' + opt_name
    value = tmux.get_option(full_opt_name)
    if 'unknown option' in value:
        if mandatory:
            raise Exception('Configuration option {} not defined or empty'.format(
                full_opt_name))
        else:
            return default
    return value

def get_config():
    config_file = get_config_var('config_file', mandatory=True)
    import yaml
    with open(config_file, 'r') as f:
        config = yaml.load(f)
    return config

def get_workdir():
    global _workdir
    if _workdir is not None:
        return _workdir
    _workdir = get_config_var('workdir', mandatory=True)
    if not os.path.isdir(_workdir):
        os.makedirs(_workdir)
    return _workdir

def match_lines(lines, index, patterns):
    if index + len(patterns) > len(lines):
        return False
    import itertools
    for line, pattern in itertools.izip(
            itertools.islice(lines, index, index + len(patterns)),
            patterns):
        if not re.search(pattern, line):
            return False
    return True

def get_context(config, silent=False):
    pane = tmux.capture_pane1()
    for ctx in config['contexts']:
        for pattern in ctx['patterns']:
            search_pattern = pattern + '(?P<cmdline>.*)$'
            m = re.search(search_pattern, pane)
            if m:
                cmd = m.group('cmdline').strip()
                log_info(
                    'Matched context "{}" with pattern "{}" and command "{}"',
                    ctx['name'], pattern, cmd)
                return ctx, pattern, cmd
    if silent:
        return None, None, None
    else:
        raise Exception('Matching context not found')

def get_prompt_input(config, last_prompt_pattern):
    last_line = tmux.capture_pane(max_lines=1)
    m = re.search(last_prompt_pattern, last_line)
    return last_line[m.end(0):].strip()

def run_command(command, input=None):
    import subprocess
    if isinstance(command, str):
        import shlex
        command = shlex.split(command)
    import pipes
    log_debug('Running ' + ' '.join(map(pipes.quote, map(str, command))))
    if input is None:
        return subprocess.check_output(command)
    else:
        print input
    proc = subprocess.Popen(command,
                     stdout=subprocess.PIPE,
                     stdin=None,
                     stderr=subprocess.STDOUT)
    out, err = proc.communicate(input=input)
    if proc.returncode != 0:
        raise subprocess.CalledProcessError('{} exited with status {}'.format(
            command[0], proc.returncode))
    return out

