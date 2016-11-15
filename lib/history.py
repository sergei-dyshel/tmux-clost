#!/usr/bin/env python

import os.path
import os

import common

from . import environment

def get_history_path(context):
    history_dir = environment.get_var('history_dir')
    if not os.path.isdir(history_dir):
        os.makedirs(history_dir)
    return os.path.join(history_dir, context)

def save_to_history(context, cmd):
    history_path = get_history_path(context)
    with open(history_path) as f:
        lines = f.readlines()
    with open(history_path, 'w') as f:
        f.write(cmd + '\n')
        f.writelines(line for line in lines if line != cmd + '\n')
