import tmux
import sys
import os.path
import os

import log

try:
    import re2 as re
except ImportError:
    import re

_workdir = None

class Error(Exception):
    def __init__(self, msg, *args, **kwargs):
        if args or kwargs:
            full_msg = msg.format(*args, **kwargs)
        else:
            full_msg = msg
        super(Error, self).__init__(full_msg)

def get_temp_file(name):
    tmp = '/tmp' # TODO: consider TMPDIR
    clost_tmp = os.path.join(tmp, 'tmux-clost')
    if not os.path.exists(clost_tmp):
        os.makedirs(clost_tmp)
    return os.path.join(clost_tmp, name)


def get_config_var(opt_name, default=None, mandatory=False):
    full_opt_name = '@clost_' + opt_name
    value = tmux.get_option(full_opt_name)
    if not value:
        if mandatory:
            raise Exception('Configuration option {} not defined or empty'.format(
                full_opt_name))
        else:
            return default
    return value

config = None
def get_config():
    global config
    if config is not None:
        return config
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

def get_context(silent=False):
    config = get_config()
    pane = tmux.capture_pane()
    for ctx in config['contexts']:
        for pattern in ctx['patterns']:
            search_pattern = '(?:^|\n)' + pattern + '(?: (?P<cmdline>.*))?$'
            m = re.search(search_pattern, pane)
            if m:
                cmd = (m.group('cmdline') or '').strip()
                log.info(
                    'Matched context "{}" with pattern "{}" and command "{}"',
                    ctx['name'], pattern, cmd)
                return ctx, pattern, cmd
    if silent:
        return None, None, None
    else:
        raise Exception('Matching context not found')
