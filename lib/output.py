#!/usr/bin/env python

import os.path

import tmux
import common
import utils
import log

DEFAULT_MAX_LINES = 10000

def copy_xsel(text=None, file=None):
    cmd = 'xsel --input --clipboard'
    if file is not None:
        cmd = 'cat {} | {}'.format(file, cmd)
    return utils.run_command(cmd, shell=True, input=text).stdout

def copy_xclip(text=None, file=''):
    cmd = 'xclip -selection clipboard {}'.format(file)
    #  http://stackoverflow.com/questions/19101735/keyboard-shortcuts-in-tmux-deactivated-after-using-xclip/21190234#21190234
    return utils.run_command(cmd, shell=True, pipe=False, input=text)

def copy_to_clipboard(out):
    # fixes problems with improper characters (such as line endings)
    # out = unicode(out, encoding='utf8', errors='ignore')
    copy_xclip(text=out)

def file_to_clipboard(path):
    copy_xclip(file=path)

def get(ctx, pattern):
    config = common.get_config()
    max_lines = config.get('max_lines', DEFAULT_MAX_LINES)
    full_out_path = os.path.join(common.get_workdir(), 'full_output.txt')
    lines = tmux.capture_pane(max_lines=max_lines, filename=full_out_path)
    return find_out_regex(pattern, lines)

def find_out(pattern, lines):
    parts = common.re.split(pattern, lines)
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
