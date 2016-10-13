import tmux
import sys
import os.path
import re
import os

import log

reload(sys)
sys.setdefaultencoding('utf8')

try:
    import re2 as re
except ImportError:
    import re

ERROR_TIMEOUT = 5000
_workdir = None

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
            log.error(traceback.format_exc())
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
            search_pattern = '\n' + pattern + '(?P<cmdline>.*)$'
            m = re.search(search_pattern, pane)
            if m:
                cmd = m.group('cmdline').strip()
                log.info(
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
