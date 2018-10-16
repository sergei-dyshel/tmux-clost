import regex

from . import log, utils

def run(command, **kwargs):
    return utils.run_command(['tmux'] + command, **kwargs).stdout.rstrip('\n')


def capture_pane(start=None,
                 dump=False,
                 end=None,
                 filename=None,
                 join=False,
                 escape=False,
                 target=None):
    cmd = ['capture-pane']
    if join:
        cmd.append('-J')
    if escape:
        cmd.append('-e')
    if dump:
        cmd.append('-p')
    if target:
        cmd += ['-t', target]
    if start is not None:
        cmd += ['-S', start]
    if end is not None:
        cmd += ['-E', end]
    return run(cmd)


def get_buffer():
    return run(['save-buffer', '-'])


def capture_lines(start=None, join=True, **kwargs):
    out = capture_pane(start=start, dump=True, join=join, **kwargs)
    rest, last_line = out.rsplit('\n', 1)

    m = regex.search(r'\[ \S+ \].*$', last_line)
    if m is not None:
        log.debug('stripping screen/tmux statusline')
        out = rest
    out = out.rstrip()
    num_lines = out.count('\n') + 1
    log.debug('Captured {} lines: {}', num_lines, repr(utils.shorten(out, 4096)))
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
    run(cmd)


def backspace(count=1):
    send_keys(['BSpace'] * count)


def display_message(msg, stdout=False, pane=None):
    cmd = ['display-message']
    if stdout:
        cmd.append('-p')
    if pane:
        cmd += ['-t', pane]
    cmd.append(msg)
    return run(cmd)


def print_message(msg, **kwargs):
    return display_message(msg, stdout=True, **kwargs)


def get_variable(var_name, **kwargs):
    return print_message('#{%s}' % var_name, **kwargs).strip()


def bind_key(key, command, table=None):
    cmd = ['bind-key']
    if table:
        cmd.extend(['-T', table])
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


def set_option(name,
               value,
               global_=False,
               window=False,
               target=None,
               clost=False):
    cmd = ['set-option']
    if global_:
        cmd += ['-g']
    if window:
        cmd += ['-w']
    if target:
        cmd += ['-t', target]
    if clost:
        name = '@clost_' + name

    if value is None:
        cmd += ['-u', name]
    else:
        cmd += [name, value]

    return run(cmd)


def unset_option(name, **kwargs):
    return set_option(name, None, **kwargs)


def get_option(name, global_=False, window=False, target=None, clost=False):
    cmd = ['show-options', '-v', '-q']
    if global_:
        cmd += ['-g']
    if window:
        cmd += ['-w']
    if target:
        cmd += ['-t', window]
    if clost:
        name = '@clost_' + name

    return run(cmd + [name]).strip()


def get_env(name):
    try:
        out = run(['show-environment', '-g', name]).strip()
        return out.split('=', 1)[1]
    except utils.RunError as err:
        if (err.result.returncode == 1
                    and 'unknown variable' in err.result.stderr):
            return None
        raise


def set_env(name, value):
    return run(['set-environment', '-g', name, value]).strip()


def replace_cmd_line(new_text, bracketed=False):
    send_keys(['C-e', 'C-u'])
    insert_text(new_text, bracketed=bracketed)


def list_panes(session=False, target=None):
    cmd = ['list-panes', '-F', '#{pane_id}']
    if target:
        cmd += ['-t', target]
    out = run(cmd)
    lines = out.splitlines()
    return lines


# TODO: not used
def list_windows(fields=['window_id']):
    fmt_str = '\t'.join(['#{%s}' % f for f in fields])
    cmd = ['list-windows', '-F', fmt_str]
    out = run(cmd)
    lines = out.splitlines()
    return [tuple(line.split('\t')) for line in lines]


def set_hook(hook, command, global_=False, session=None):
    cmd = ['set-hook']
    if global_:
        cmd += ['-g']
    if session:
        cmd += ['-t', session]
    cmd += [hook, command]
    return run(cmd)


