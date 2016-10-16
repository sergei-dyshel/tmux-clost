#!/usr/bin/env python

import tmux
import common
import os.path
import sys
import os
import utils

import log

KEY_TABLE = 'clost'

def bind_key_to_cmd(key, cmd, background=False, **kwargs):
    main_script = os.path.abspath(sys.argv[0])
    bind_cmd = ['run-shell']
    if background:
        bind_cmd.append('-b')
    bind_cmd.append('{} {}'.format(main_script, cmd))
    tmux.bind_key(key, bind_cmd, key_table=KEY_TABLE, **kwargs)
    log.info('Bound "{}" to "{}"', key, cmd)

def bind_enter():
    if not common.get_config_var('save_to_history'):
        return
    tmux.bind_key('Enter', ['send-keys', 'Enter'])
    bind_key_to_cmd(
        'Enter', 'save_to_history', no_prefix=True, background=True)
    log.info('Bound "Enter" to save history')

def unbind_enter():
    return tmux.unbind_key('Enter', no_prefix=True)

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

