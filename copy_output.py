#!/usr/bin/env python

import tmux
import common
import itertools
import os.path

def main():
    config = common.get_config()
    lines = tmux.capture_pane(max_lines=-1, till_cursor=True, splitlines=True)
    ctx_name, ctx_conf = common.find_context(lines, config)
    if ctx_name is None:
        raise Exception('Matching context not found')
    patterns = ctx_conf['patterns']
    last = None
    i = len(lines) - 2 * len(patterns)
    while i >= 0:
        if common.match_lines(lines, i, patterns):
            if last is not None:
                tmux.display_message(
                    'copied {} lines (context: {})'.format(last - i, ctx_name))
                out = ''.join(itertools.islice(lines, i, last))
                with open(os.path.join(common.get_workdir(), 'output.txt'), 'w') as f:
                    f.write(out)

                import sys
                # prevent pyperclip from using Gtk/Qt clipboard
                sys.modules['gtk'] = None
                sys.modules['PyQt4'] = None
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
