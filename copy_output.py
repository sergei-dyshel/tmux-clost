#!/usr/bin/env python

import tmux
import common
import itertools
import os.path
import utils

DEFAULT_MAX_LINES = 10000

def copy_xsel(text, selection):
    return utils.run_command('xsel --input --{}'.format(selection), input=text)

def copy_to_clipboard(out):
    # fixes problems with improper characters (such as line endings)
    out_utf8 = unicode(out, encoding='utf8', errors='ignore')
    for selection in ['primary', 'clipboard']:
        copy_xsel(out_utf8.encode('utf-8'), selection)

def main(argv):
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
                out = ''.join(itertools.islice(lines, i, last))
                save_path = os.path.join(common.get_workdir(), 'output.txt')
                with open(save_path, 'w') as f:
                    f.write(out)

                if len(argv) < 2 or argv[1] != '--save-only':
                    copy_to_clipboard(out)
                    action = 'Copied'
                else:
                    action = 'Saved to ' + save_path

                tmux.display_message('{} {} lines (context: {})'.format(
                    action, last - i, ctx_name))

                break
            i -= len(patterns)
        else:
            if last is None:
                last = i + len(patterns)
            i -= 1

if __name__ == '__main__':
    common.wrap_main(main)
