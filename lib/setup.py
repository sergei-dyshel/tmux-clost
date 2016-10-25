#!/usr/bin/env python

import tmux
import common
import os.path
import sys
import os
import utils

import log

def bind_enter():
    if not common.get_config()['intercept_enter']:
        return
    tmux.bind_key('Enter', ['send-keys', 'Enter'])
    tmux.bind_key(
        'Enter', ['run-shell', '-b', 'clost save_to_history'], no_prefix=True)
    log.info('Bound "Enter" to save history')

def unbind_enter():
    return tmux.unbind_key('Enter', no_prefix=True)
