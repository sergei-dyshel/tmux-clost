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
    ctx, pattern, cmd = common.get_context(config)

    max_lines = config.get('max_lines', DEFAULT_MAX_LINES)
    full_out_path = os.path.join(common.get_workdir(), 'full_output.txt')
    lines = tmux.capture_pane1(max_lines=max_lines, filename=full_out_path)
    save_path = os.path.join(common.get_workdir(), 'output.txt')

    parts = common.re.split(pattern, lines)
    out = None
    for part in reversed(parts):
        part = part.strip()
        num_lines = part.count('\n') + 1
        if num_lines == 1:
            common.log_debug('Skipping command "{}"', part)
            continue
        out = part
        break
    if out is None:
        raise Exception('No output to copy')

    with open(save_path, 'w') as f:
        f.write(out)

    if len(argv) < 2 or argv[1] != '--save-only':
        file_to_clipboard(save_path)
        action = 'Copied'
    else:
        action = 'Saved to ' + save_path

    tmux.display_message('{} {} lines (context: {})'.format(
        action, num_lines, ctx['name']))

if __name__ == '__main__':
    common.wrap_main(main)
