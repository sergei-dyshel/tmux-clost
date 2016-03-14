#!/usr/bin/env python

import tmux
import common
import itertools
import re
import os.path

def match_lines(lines, index, patterns):
    if index + len(patterns) > len(lines):
        return False
    for line, pattern in itertools.izip(
            itertools.islice(lines, index, index + len(patterns)),
            patterns):
        if not re.search(pattern, line):
            return False
    return True

def find_context(lines, config):
    for ctx_name, ctx_conf in config['contexts'].iteritems():
        patterns = ctx_conf['patterns']
        print len(patterns)
        if match_lines(lines, len(lines) - len(patterns), patterns):
            return ctx_name, ctx_conf
    return None, None

def main():
    config = common.get_config()
    lines = tmux.capture_pane(max_lines=-1, till_cursor=True, splitlines=True)
    ctx_name, ctx_conf = find_context(lines, config)
    if ctx_name is None:
        raise Exception('Matching context not found')
    patterns = ctx_conf['patterns']
    last = None
    i = len(lines) - 2 * len(patterns)
    while i >= 0:
        if match_lines(lines, i, patterns):
            if last is not None:
                tmux.display_message(
                    'copied {} lines (context: {})'.format(last - i, ctx_name))
                out = ''.join(itertools.islice(lines, i, last))
                with open(os.path.join(common.get_workdir(), 'output.txt'), 'w') as f:
                    f.write(out)
                import pyperclip
                pyperclip.copy(out)
                break
            i -= len(patterns)
        else:
            if last is None:
                last = i + len(patterns)
            i -= 1

if __name__ == '__main__':
    common.wrap_main(main)
