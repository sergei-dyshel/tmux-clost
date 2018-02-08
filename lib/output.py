#!/usr/bin/env python

import os.path
import regex

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
    return find_out_regex(pattern, lines)

# uses REVERSE search in regex module
# slower than regex.split
def find_out_regex(pattern, lines):
    end = len(lines)
    for match in regex.finditer(pattern, lines, regex.REVERSE):
        out = lines[match.end():end].rstrip('\n')
        if '\n' in out:
            return out
        else:
            end = match.start()
            # Skipping command
    raise Exception('No output to copy')

