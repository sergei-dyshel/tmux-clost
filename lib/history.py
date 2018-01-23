#!/usr/bin/env python

import os.path
import os
import contextlib

import common

from . import environment, gen_history

def get_history_path(context):
    history_dir = environment.get_var('history_dir')
    if not os.path.isdir(history_dir):
        os.makedirs(history_dir)
    return os.path.join(history_dir, context)

def save_to_history(context, cmd):
    history_path = get_history_path(context)
    hist_dir = os.path.dirname(history_path)
    # TODO: make a util function
    if not os.path.isdir(hist_dir):
        try:
            os.makedirs(hist_dir)
        except OSError:
            pass
    if os.path.isfile(history_path):
        with open(history_path) as f:
            lines = f.readlines()
    else:
        lines = []
    with open(history_path, 'w') as f:
        f.write(gen_history.current_line(cmd) + '\n')
        f.writelines(
            line for line in lines
            if gen_history.parse_line(
                line, cmd_only=True) != cmd)
