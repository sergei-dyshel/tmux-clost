import tmux
import sys
reload(sys)
sys.setdefaultencoding('utf8')

try:
    import re2 as re
except ImportError:
    import re

ERROR_TIMEOUT = 5000

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
            traceback.print_exc(file=sys.stdout)
            import inspect
            import os.path
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
    workdir = get_config_var('workdir', mandatory=True)
    import os.path
    import os
    if not os.path.isdir(workdir):
        os.makedirs(workdir)
    return workdir

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

def _find_context(lines, config):
    for ctx_name, ctx_conf in config['contexts'].iteritems():
        patterns = ctx_conf['patterns']
        if match_lines(lines, len(lines) - len(patterns), patterns):
            return ctx_name, ctx_conf
    return None, None

def get_context(config, silent=False):
    max_prompt_lines = max(len(context['patterns'])
                           for context in config['contexts'].itervalues())
    lines = tmux.capture_pane(max_lines=max_prompt_lines,
                              till_cursor=True,
                              splitlines=True)
    ctx_name, ctx_conf = _find_context(lines, config)
    if ctx_name is None and not silent:
        raise Exception('Matching context not found')
    return ctx_name, ctx_conf

def get_prompt_input(config, last_prompt_pattern):
    last_line = tmux.capture_pane(max_lines=1)
    m = re.search(last_prompt_pattern, last_line)
    return last_line[m.end(0):].strip()

def run_command(command, input=''):
    import subprocess
    if isinstance(command, str):
        import shlex
        command = shlex.split(command)
    import pipes
    print 'Running ' + ' '.join(map(pipes.quote, map(str, command)))
    proc = subprocess.Popen(command,
                     stdout=subprocess.PIPE,
                     stdin=subprocess.PIPE,
                     stderr=subprocess.STDOUT)
    out, err = proc.communicate(input=input)
    if proc.returncode != 0:
        raise subprocess.CalledProcessError('{} exited with status {}'.format(
            command[0], proc.returncode))
    return out

