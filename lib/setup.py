#!/usr/bin/env python

import tmux
import common
import os.path
import sys
import os
import utils

import log

def bind_key_to_cmd(key, cmd, background=False, **kwargs):
    main_script = os.path.abspath(sys.argv[0])
    bind_cmd = ['run-shell']
    if background:
        bind_cmd.append('-b')
    bind_cmd.append('{} {}'.format(main_script, cmd))
    tmux.bind_key(key, bind_cmd, **kwargs)
    log.info('Bound "{}" to "{}"', key, cmd)

def bind_enter():
    if not common.get_config()['intercept_enter']:
        return
    tmux.bind_key('Enter', ['send-keys', 'Enter'])
    bind_key_to_cmd(
        'Enter', 'save_to_history', no_prefix=True, background=True)
    log.info('Bound "Enter" to save history')

def unbind_enter():
    return tmux.unbind_key('Enter', no_prefix=True)
