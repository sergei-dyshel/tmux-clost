def run_tmux(cmd_and_args, input=''):
    import subprocess
    if isinstance(cmd_and_args, str):
        import shlex
        cmd_and_args = shlex.split(cmd_and_args)
    full_cmd = ['tmux'] + map(str, cmd_and_args)
    import pipes
    print 'Running ' + ' '.join(map(pipes.quote, map(str, full_cmd)))
    proc = subprocess.Popen(full_cmd,
                     stdout=subprocess.PIPE,
                     stdin=subprocess.PIPE,
                     stderr=subprocess.STDOUT)
    out, _ = proc.communicate(input=input)
    return out

def capture_pane(max_lines=0, till_cursor=False, splitlines=False):
    cursor_x = int(get_variable('cursor_x'))
    cursor_y = int(get_variable('cursor_y'))
    pane_height = int(get_variable('pane_height'))
    pane_width = int(get_variable('pane_width'))
    print 'pane_height {} cursor_y {}'.format(pane_height, cursor_y)
    start = -max_lines if max_lines >= 0 else '-'
    cmd = ['capture-pane', '-J']
    cmd += ['-S', start]
    cmd += ['-E', cursor_y]
    run_tmux(cmd)

    out = run_tmux(['save-buffer', '-'])
    run_tmux(['delete-buffer'])

    trim_lines = pane_height - cursor_y - 1
    if (trim_lines > 0) or max_lines > 0 or till_cursor or splitlines:
        out_lines = out.splitlines(True)
        last_line = out_lines[-1]
        if trim_lines > 0:
            out_lines = out_lines[:-trim_lines]
        if max_lines > 0:
            out_lines = out_lines[-max_lines:]
        trim_chars = len(last_line) - cursor_x
        if till_cursor and (len(last_line) < pane_width) and (trim_chars > 0):
            out_lines[-1] = last_line[:-(trim_chars)]

        out = ''.join(out_lines) if not splitlines else out_lines

    return out

def insert_text(text):
    run_tmux(['load-buffer', '-'], input=text)
    run_tmux(['paste-buffer'])
    run_tmux(['delete-buffer'])

def backspace(count=1):
    keys = ['BSpace'] * count
    run_tmux(['send-keys'] + keys)

def _display_message(msg, stdout=False):
    cmd = ['display-message']
    if stdout:
        cmd.append('-p')
    cmd.append(msg)
    return run_tmux(cmd)

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

def tmux_bind_key(key, cmd):
    run_tmux(['bind-key', key] + cmd)

def get_option(opt_name):
    return run_tmux(['show-options', '-g', '-v', opt_name]).strip()

def set_option(name, value):
    return run_tmux(['set-option', '-g'] + (['-u', name] if value is None else
                                            [name, value]))
