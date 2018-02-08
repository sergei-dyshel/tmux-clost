import regex

from .config import config
from . import log, tmux, common

class Context(object):
    def __init__(self,
                 cfg=None,
                 pattern=None,
                 cmd_line=None,
                 match=None):
        self.cfg = cfg
        self.cmd_line = cmd_line
        self.pattern = pattern
        self.match = match
        self.options = config.options.copy()
        self.options.update(cfg['options'])

    @property
    def name(self):
        return self.cfg['name']

    def get_output(self):
        lines = tmux.capture_lines(start=-self.options['max_lines'])
        end = len(lines)
        for match in regex.finditer(self.pattern, lines, regex.REVERSE):
            out = lines[match.end():end].rstrip('\n')
            if '\n' in out:
                return out.split('\n', 1)[1]
            else:
                end = match.start()
                # Skipping command
        raise Exception('No output to copy')

ESCAPE_CODE_RE = r'((?:\x9B|\x1B\[)[0-?]*[ -\/]*[@-~])'
def capture_escaped_line():
    y = tmux.get_variable('cursor_y')
    line = tmux.capture_pane(start=y, join=True, dump=True, escape=True).rstrip()
    splits = regex.split(ESCAPE_CODE_RE, line)
    splits = [s for s in splits if s]
    return line, splits

def is_escape_code(s):
    return regex.match(ESCAPE_CODE_RE, s)

def named_group(name, regex):
    return '(?P<{}>{})'.format(name, regex)

def get_current(target=None):
    pane_lines = tmux.capture_lines(target=target)
    for ctx_cfg in config.contexts:
        for pattern in ctx_cfg['patterns']:
            search_pattern = pattern + '(?: (?P<cmdline>.*))?$'
            m = regex.search(search_pattern, pane_lines, regex.REVERSE)
            if not m:
                continue
            cmd = (m.group('cmdline') or '').strip()
            log.info(
                'Matched context "{}" with pattern "{}" and command "{}"',
                ctx_cfg['name'], pattern, cmd)
            return Context(cfg=ctx_cfg, pattern=pattern, cmd_line=cmd, match=m)
    return None

def finditer_prompts(text, pattern):
    search_pattern = '(?:^|\n)' + named_group('pattern', pattern)
    for match in regex.finditer(search_pattern, text):
        yield common.Namespace(
            start=match.start('pattern'), end=match.end('pattern'))
