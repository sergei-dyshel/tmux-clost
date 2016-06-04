#!/usr/bin/env python

import tmux
import common
import os.path
import sys
import os
import utils

def script_path(name):
    return os.path.abspath(os.path.join(os.path.dirname(sys.argv[0]), name))

def bind_key_to_function(function, script=None, script_args=''):
    workdir = common.get_workdir()
    key = common.get_config_var(function + '_key')
    if script is None:
        script = function
    if key is not None:
        tmux.tmux_bind_key(
            key, ['run-shell',
                  '{} {} >{}/last.log 2>&1'.format(
                      script_path(script + '.py'), script_args, workdir)])

def bind_enter():
    workdir = common.get_workdir()
    if not common.get_config_var('save_to_history'):
        return
    shell_cmd = ['run-shell', '-b', '{} >{}/last.log 2>&1'.format(
                script_path('save_to_history.py'), workdir)]
    tmux.tmux_bind_key('Enter', shell_cmd, no_prefix=True)

def unbind_enter():
    return tmux.tmux_bind_key('Enter', no_prefix=True, unbind=True)

def run_fzf(input):
    unbind_enter()
    try:
        line = utils.run_command(
            ['fzf-tmux', '-d', '20%', '--no-sort'],
            input=input)
        if len(line.splitlines()) > 1:
            print 'fzf-tmux returned unexpected output: \n' + line
            raise Exception('fzf-tmux returned unexpected output')
    finally:
        bind_enter()
    line = line.strip()
    return line

def main(argv):
    bind_key_to_function('copy_output')
    bind_key_to_function('save_output', 'copy_output', '--save-only')
    bind_key_to_function('search_history')
    bind_key_to_function('insert_snippet')
    bind_enter()

if __name__ == '__main__':
    common.wrap_main(main)

