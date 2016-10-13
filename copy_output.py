#!/usr/bin/env python

import tmux
import common
import os.path
import utils

import log

DEFAULT_MAX_LINES = 10000

def copy_xsel(text, selection):
    return utils.run_command('xsel --input --{}'.format(selection), input=text).stdout

def copy_to_clipboard(out):
    # fixes problems with improper characters (such as line endings)
    out_utf8 = unicode(out, encoding='utf8', errors='ignore')
    for selection in ['primary', 'clipboard']:
        copy_xsel(out_utf8, selection)

def file_to_clipboard(path):
    utils.run_command(
        'cat {} | xsel -ib'.format(path),
        shell=True)

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
            log.debug('Skipping command "{}"', part)
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
