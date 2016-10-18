#!/usr/bin/env python

import os.path
import os

import common

def get_history_path(context):
    workdir = common.get_workdir()
    history_dir = os.path.join(workdir, 'history')
    if not os.path.isdir(history_dir):
        os.makedirs(history_dir)
    return os.path.join(history_dir, context)

def save_to_history(context, line):
    history_path = get_history_path(context)
    with open(history_path, 'a') as f:
        f.write(line + os.linesep)

def remove_duplicates(lines):
    lines_met = set()
    for i in reversed(xrange(len(lines))):
        line = lines[i]
        if line in lines_met:
            del lines[i]
        else:
            lines_met.add(line)

def load_history(context):
    history_path = get_history_path(context)
    with open(history_path, 'r') as f:
        lines = f.read().splitlines(True)
    remove_duplicates(lines)
    with open(history_path, 'w') as f:
        f.writelines(lines)
    return reversed(lines)

