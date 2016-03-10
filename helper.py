#!/usr/bin/env python

import os.path
import sys
import pipes

def run_tmux(cmd_and_args, input=''):
    import subprocess
    if isinstance(cmd_and_args, str):
        import shlex
        cmd_and_args = shlex.split(cmd_and_args)
    full_cmd = ['tmux'] + map(str, cmd_and_args)
    print 'Running ' + ' '.join(map(pipes.quote, map(str, full_cmd)))
    proc = subprocess.Popen(full_cmd,
                     stdout=subprocess.PIPE,
                     stdin=subprocess.PIPE,
                     stderr=subprocess.STDOUT)
    out, _ = proc.communicate(input=input)
    return out

def capture_pane(max_lines=0, till_cursor=False):
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
    if (trim_lines > 0) or max_lines > 0 or till_cursor:
        out_lines = out.splitlines(True)
        last_line = out_lines[-1]
        if trim_lines > 0:
            out_lines = out_lines[:-trim_lines]
        if max_lines > 0:
            out_lines = out_lines[-max_lines:]
        trim_chars = len(last_line) - cursor_x
        if till_cursor and (len(last_line) < pane_width) and (trim_chars > 0):
            out_lines[-1] = last_line[:-(trim_chars)]

        out = ''.join(out_lines)

    return out

def insert_text(text):
    run_tmux(['load-buffer', '-'], input=text)
    run_tmux(['paste-buffer'])
    run_tmux(['delete-buffer'])

def backspace(count=1):
    keys = ['BSpace'] * count
    run_tmux(['send-keys'] + keys)

def tmux_display_message(msg, stdout=False):
    cmd = ['display-message']
    if stdout:
        cmd.append('-p')
    cmd.append(msg)
    return run_tmux(cmd)

def get_variable(var_name):
    return tmux_display_message('#{%s}' % var_name, stdout=True)

def tmux_bind_key(key, cmd):
    run_tmux(['bind-key', key] + cmd)

def setup(args):
    tmux_bind_key('a', ['run-shell', '{} copy >/home/sergei/tmux-helper/last.log 2>&1'.format(os.path.abspath(sys.argv[0]))])

def copy(args):
    # insert_text("hello`hello`")
    # backspace(3)
    with open(os.path.expanduser('~/temp/history.txt'), 'w') as f:
        f.write(capture_pane(till_cursor=True))
    # blabla()

def main():
    import argparse
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers()

    setup_parser = subparsers.add_parser('setup')
    setup_parser.set_defaults(func=setup)

    copy_parser = subparsers.add_parser('copy')
    copy_parser.set_defaults(func=copy)

    args = parser.parse_args()
    print 'Invoked with args: ' + ' '.join(map(pipes.quote, sys.argv))
    args.func(args)

def entry_point():
    try:
        main()
    except BaseException as exc:
        if sys.stdin.isatty():
            # executed by user
            raise
        else:
            # executed by tmux
            import traceback
            traceback.print_exc(file=sys.stdout)
            tmux_display_message('Clost: Python failed with {}: {}'.format(
                exc.__class__.__name__, exc))

if __name__ == '__main__':
    entry_point()

