#!/usr/bin/env python

import tmux
import common
import os.path
import sys
import os

def script_path(name):
    return os.path.abspath(os.path.join(os.path.dirname(sys.argv[0]), name))

def bind_key_to_function(function):
    workdir = common.get_workdir()
    key = common.get_config_var(function + '_key')
    if key is not None:
        tmux.tmux_bind_key(
            key, ['run-shell',
                  '{} >{}/last.log 2>&1'.format(
                      script_path(function + '.py'), workdir)])

def bind_enter():
    workdir = common.get_workdir()
    if not common.get_config_var('save_to_history'):
        return
    shell_cmd = ['run-shell', '{} >{}/last.log 2>&1'.format(
                script_path('save_to_history.py'), workdir)]
    send_enter_cmd = ['send-keys', 'Enter']
    cmd = shell_cmd + ['\;'] + send_enter_cmd
    tmux.tmux_bind_key('Enter', cmd, no_prefix=True)

def unbind_enter():
    return tmux.tmux_bind_key('Enter', no_prefix=True, unbind=True)

def main():
    bind_key_to_function('copy_output')
    bind_key_to_function('search_history')
    bind_enter()

    # config_file = common.get_config_var('config_file', mandatory=True)

if __name__ == '__main__':
    common.wrap_main(main)

