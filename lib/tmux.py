import utils

import log

def _run(command=[], **kwargs):
    return utils.run_command(['tmux'] + command, **kwargs).stdout

def _truncate_middle(string):
    string = string.strip('\n')
    if len(string) <= 40:
        return string
    else:
        return string[:20] + '...' + string[-20:]

def capture_pane(max_lines=0, filename=None):
    start = -max_lines if max_lines >= 0 else '-'
    cmd = ['capture-pane', '-J']
    cmd += ['-S', start]
    _run(cmd)

    if filename is not None:
        log.debug('Captured to {}', filename)
        _run(['save-buffer', filename])
        with open(filename) as f:
            out = f.read()
    else:
        out = _run(['save-buffer', '-'])

    _run(['delete-buffer'])

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


def insert_text(text):
    _run(['load-buffer', '-'], input=text)
    _run(['paste-buffer', '-d', '-r'])

def send_keys(keys, literally=False):
    cmd = ['send-keys']
    if literally:
        cmd.append('-l')
    cmd.extend(keys)
    _run(cmd)

def backspace(count=1):
    send_keys(['BSpace'] * count)

def _display_message(msg, stdout=False):
    cmd = ['display-message']
    if stdout:
        cmd.append('-p')
    cmd.append(msg)
    return _run(cmd)

def print_message(msg):
    return _display_message(msg, stdout=True)

def display_message(msg, timeout=None):
    if timeout is not None:
        orig_display_time = get_option('display-time')
        set_option('display-time', timeout)
    _display_message(msg)
    if timeout is not None:
        import time
        time.sleep(timeout / 1000.0)
        set_option('display-time', orig_display_time)

def get_variable(var_name):
    return print_message('#{%s}' % var_name)

def bind_key(key, command, no_prefix=False, key_table=None):
    cmd = ['bind-key']
    if no_prefix:
        cmd.append('-n')
    if key_table:
        cmd.extend(['-T', key_table])
    cmd.append(key)
    cmd.extend(command)
    _run(cmd)

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
    _run(cmd, ignore_err=r"table .* doesn't exist")

def get_option(opt_name):
    return _run(['show-options', '-g', '-v', '-q', opt_name]).strip()

def set_option(name, value):
    return _run(['set-option', '-g'] + (['-u', name]
                                        if value is None else [name, value]))

def replace_cmd_line(new_text):
    send_keys(['C-e', 'C-u'])
    send_keys([new_text], literally=True)
