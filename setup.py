#!/usr/bin/env python

import tmux
import common
import os.path
import sys
import os
import utils

import log

def script_path(name):
    return os.path.abspath(os.path.join(os.path.dirname(sys.argv[0]), name))

def bind_key_to_function(function, script=None, script_args=''):
    workdir = common.get_workdir()
    key = common.get_config_var(function + '_key')
    if script is None:
        script = function
    if key is not None:
        tmux.bind_key(
            key, ['run-shell',
                  '{} {}'.format(
                      script_path(script + '.py'), script_args)])

def bind_enter():
    workdir = common.get_workdir()
    if not common.get_config_var('save_to_history'):
        return
    shell_cmd = ['run-shell', '-b', '{}'.format(
                script_path('save_to_history.py'))]
    tmux.bind_key('Enter', shell_cmd, no_prefix=True)

def unbind_enter():
    return tmux.bind_key('Enter', no_prefix=True, unbind=True)

def run_fzf(input):
    unbind_enter()
    try:
        fzf_res = utils.run_command(
            ['fzf-tmux', '-d', '20%', '--no-sort'],
            returncodes=[0, 130],
            input=input)
        if fzf_res.returncode == 130:
            line = ''
        else:
            line = fzf_res.stdout
            if len(line.splitlines()) > 1:
                log.error('fzf-tmux returned unexpected output: \n' + line)
                raise Exception('fzf-tmux returned unexpected output')
    finally:
        bind_enter()
    line = line.strip()
    return line


def main(argv):
    bind_enter()
    if len(sys.argv) > 1 and sys.argv[1] == 'bind_enter':
        return
    bind_key_to_function('copy_output')
    bind_key_to_function('save_output', 'copy_output', '--save-only')
    bind_key_to_function('search_history')
    bind_key_to_function('insert_snippet')

if __name__ == '__main__':
    common.wrap_main(main)

