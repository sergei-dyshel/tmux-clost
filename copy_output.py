#!/usr/bin/env python

import tmux
import common
import itertools
import os.path

DEFAULT_MAX_LINES = 10000

def main():
    config = common.get_config()
    ctx_name, ctx_conf = common.get_context(config)

    max_lines = config.get('max_lines', DEFAULT_MAX_LINES)
    lines = tmux.capture_pane(max_lines=max_lines, till_cursor=True, splitlines=True)
    patterns = ctx_conf['patterns']
    last = None
    i = len(lines) - 2 * len(patterns)
    while i >= 0:
        if i == 0 or common.match_lines(lines, i, patterns):
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
