#!/usr/bin/env python

import tmux
import common
import os.path
import sys
import os
import utils

import log

def bind_key_to_cmd(key, args, background=False, **kwargs):
    main_script = sys.argv[0]
    bind_cmd = ['run-shell']
    if background:
        bind_cmd.append('-b')
    bind_cmd.append('{} {}'.format(main_script, args))
    return tmux.bind_key(key, bind_cmd, **kwargs)

def bind_cmd_if_defined(cmd, **kwargs):
    key = common.get_config_var(cmd + '_key')
    if key is None:
        return
    return bind_key_to_cmd(key, cmd, **kwargs)

def bind_enter():
    if not common.get_config_var('save_to_history'):
        return
    return bind_key_to_cmd(
        'Enter', 'save-to-history', no_prefix=True, background=True)

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

COMMANDS = ['copy_output', 'insert_snippet', 'search_history']

def main(argv):
    bind_enter()
    for cmd in COMMANDS:
        bind_cmd_if_defined(cmd)

if __name__ == '__main__':
    common.wrap_main(main)

