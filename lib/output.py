#!/usr/bin/env python

import os.path
import re

import tmux
import common
import utils
import log

from . import config

DEFAULT_MAX_LINES = 10000

def get(pattern, max_lines=None):
    # full_out_path = os.path.join(common.get_workdir(), 'full_output.txt')
    # lines = tmux.capture_pane(max_lines=max_lines, filename=full_out_path)
    lines = tmux.capture_lines(start=-max_lines)
    return find_out(pattern, lines)

def find_out(pattern, lines):
    regex = re.compile(pattern)
    parts = regex.split(lines)[0::(1 + regex.groups)]
    out = None
    for part in reversed(parts):
        part = part.strip()
        num_lines = part.count('\n') + 1
        if num_lines == 1:
            # log.debug('Skipping command "{}"', part)
            continue
        out = part
        break
    if out is None:
        raise Exception('No output to copy')
    return out

# uses REVERSE search in regex module
# slower than re.split
def find_out_regex(pattern, lines):
    import regex
    end = len(lines)
    for match in regex.finditer('\n' + pattern, lines, regex.REVERSE):
        out = lines[match.end():end].rstrip('\n')
        if '\n' in out:
            return out
        else:
            end = match.start()
            # Skipping command
    raise Exception('No output to copy')

