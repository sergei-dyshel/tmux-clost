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
        copy_xsel(out_utf8, selection)

def file_to_clipboard(path):
    cnt = 0
    while (utils.run_command(
            'xsel -ob | diff -q - {}'.format(path), returncodes=[], shell=True) != 0):
        if cnt > 1:
            raise Exception('exceeded {} xsel tries'.format(cnt))
        cnt += 1
        utils.run_command(
            'cat {} | xsel -ib'.format(path),
            shell=True)
    common.log_debug('tried xsel {} times', cnt)
    # utils.run_command(
    #     'xclip -verbose -in -selection clipboard -loops 1 {}'.format(path))

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
                    file_to_clipboard(save_path)
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
