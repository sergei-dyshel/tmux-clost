import utils

from . import log

control_mode = None

class TmuxError(Exception):
    pass

def run(command, cm=False, **kwargs):
    if cm:
        global control_mode
        if control_mode is None:
            control_mode = ControlMode()
        if isinstance(command, list):
            command = utils.shlex_join(command)
            return control_mode.run(command)
    try:
        return utils.run_command(['tmux'] + command, **kwargs).stdout
    except utils.RunError as e:
        return TmuxError(e.result.stdout + e.result.stderr)

def _truncate_middle(string):
    string = string.strip('\n')
    if len(string) <= 40:
        return string
    else:
        return string[:20] + '...' + string[-20:]

def capture_pane(start=None, dump=False, end=None, filename=None, join=False, escape=False):
    cmd = ['capture-pane']
    if join:
        cmd.append('-J')
    if escape:
        cmd.append('-e')
    if dump:
        cmd.append('-p')
    if start is not None:
        cmd += ['-S', start]
    if end is not None:
        cmd += ['-E', end]
    return run(cmd)

def get_buffer():
    return run(['save-buffer', '-'])

def capture_lines(start=None, filename=None):
    capture_pane(start=start, join=True)
    if filename is not None:
        log.debug('Captured to {}', filename)
        run(['save-buffer', filename])
        with open(filename) as f:
            out = f.read()
    else:
        out = get_buffer()

    run(['delete-buffer'])

    import re
    m = re.search(r'\n\[ \S+ \].*$', out)
    if m is not None:
        log.debug('stripping screen/tmux statusline')
        out = out[:m.start()]
    out = out.rstrip('\n')
    num_lines = out.count('\n') + 1
    log.debug('Captured {} lines: "{}"', num_lines,
                       _truncate_middle(out))
    return out


def insert_text(text, bracketed=False):
    run(['load-buffer', '-'], input=text)
    cmd = ['paste-buffer', '-d', '-r']
    if bracketed:
        cmd.append('-p')
    run(cmd)

def send_keys(keys, literally=False):
    cmd = ['send-keys']
    if literally:
        cmd.append('-l')
    cmd.extend(keys)
    # for some reason send-keys does not work in control mode
    run(cmd, cm=False)

def backspace(count=1):
    send_keys(['BSpace'] * count)

def _display_message(msg, stdout=False):
    cmd = ['display-message']
    if stdout:
        cmd.append('-p')
    cmd.append(msg)
    return run(cmd)

def print_message(msg):
    return _display_message(msg, stdout=True)

def display_message(msg):
    _display_message(msg)

def get_variable(var_name):
    return print_message('#{%s}' % var_name).strip()

def bind_key(key, command, no_prefix=False, key_table=None):
    cmd = ['bind-key']
    if no_prefix:
        cmd.append('-n')
    if key_table:
        cmd.extend(['-T', key_table])
    cmd.append(key)
    cmd.extend(command)
    run(cmd)

def unbind_key(key=None, all=False, no_prefix=False, key_table=None):
    cmd = ['unbind-key']
    if all:
        cmd.append('-a')
    if no_prefix:
        cmd.append('-n')
    if key_table:
        cmd.extend(['-T', key_table])
    if key:
        cmd.append(key)
    run(cmd, ignore_err=r"table .* doesn't exist")

def pane_in_mode():
    return get_variable('pane_in_mode') == '1'

def get_option(opt_name):
    return run(['show-options', '-g', '-v', '-q', opt_name]).strip()

def get_all_options():
    raw = run(['show-options', '-g'])
    res = {}
    for line in raw.splitlines():
        name, value = line.split(' ', 1)
        value = utils.unquote(value)
        if value == 'on':
            value = True
        elif value == 'off':
            value = False
        res[name] = value
    return res

def set_option(name, value):
    return run(['set-option', '-g'] + (['-u', name]
                                        if value is None else [name, value]))
def get_env(name):
    return run(['show-environment', '-g', name]).strip()

def set_env(name, value):
    return run(['set-environment', '-g', name, value]).strip()

def replace_cmd_line(new_text, bracketed=False):
    send_keys(['C-e', 'C-u'])
    insert_text(new_text, bracketed=bracketed)

class ControlModeError(Exception):
    pass

class ControlMode(object):
    REGEX = '%begin \d+ \d+ \d+\r\n(.+?\r\n)?%(error|end) \d+ \d+ \d+\r\n'

    def __init__(self):
        import pexpect
        self.spawn = pexpect.spawn('tmux -C')
        self.spawn.delaybeforesend = None
        self.spawn.delayafterread = None
        # skip empty output
        self.spawn.expect(self.REGEX)

    def run(self, cmd):
        log.debug('Running in Tmux control mode: {}', cmd)
        self.spawn.sendline(cmd)
        self.spawn.expect(self.REGEX)
        m = self.spawn.match
        out = m.group(1)
        if out is None:
            out = ''
        out = out.replace('\r\n', '\n')
        if m.group(2) == 'error':
            raise TmuxError(out)
        else:
            return out


