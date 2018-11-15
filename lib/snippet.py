import os.path
import re
import time
import os

from . import (common, tmux, utils, log)

PATTERN = r'\{\{\{(?P<cmd>\w+)=(?P<arg>.*?)\}\}\}'
PATTERN_NO_CAPTURES = r'(\{\{\{\w+=.*?\}\}\})'

def _replacer(match):
    cmd, arg = _parse_match(match)
    if cmd == 'char':
        return chr(int(arg))
    elif cmd == 'sleep':
        # will be handled later
        return match.group(0)
    elif cmd == 'file':
        fname = os.path.expanduser(os.path.expandvars(arg))
        with open(fname, 'rb+') as f:
            return f.read()
    else:
        raise common.ClostError(
                'Error on snippet: invalid cmd "{}"'.format(cmd))

def _processor(match):
    cmd, arg = _parse_match(match)
    if cmd == 'sleep':
        seconds = float(arg)
        log.debug('Sleeping for {} seconds'.format(arg))
        time.sleep(seconds)
    else:
        raise common.ClostError(
                'Error in snippet: unexpected cmd "{}"'.format(cmd))


def _parse_match(match):
    return match.group('cmd'), match.group('arg')


def insert_snippet(snippets_dir, ctx_name, snippet_name, bracketed):
    os.environ['SNIPPETS'] = snippets_dir
    ctx_snippets_dir = os.path.join(snippets_dir, ctx_name)
    snippet_file = os.path.join(ctx_snippets_dir, snippet_name)
    with open(snippet_file, 'rb+') as f:
        text = f.read()[:-1]
    while True:
        new_text = re.sub(PATTERN, _replacer, text)
        if new_text == text:
            break
        text = new_text
    for fragment in re.split(PATTERN_NO_CAPTURES, text):
        match = re.match(PATTERN, fragment)
        if not match:
            tmux.insert_text(fragment, bracketed=bracketed)
        else:
            _processor(match)
