import re

from . import log, config, tmux, common

class Context(object):
    def __init__(self, cfg=None, pattern=None, cmd_line=None,
                 output=None, match=None, offset=None):
        self.cfg = cfg
        self.cmd_line = cmd_line
        self.pattern = pattern
        self.output = output
        self.match = match
        self.offset = offset
        self.options = config.CombinedOptions(
            config.DictOptions(self.cfg.get('options', None)),
            config.global_options)

    @property
    def name(self):
        return self.cfg['name']

ESCAPE_CODE_RE = r'((?:\x9B|\x1B\[)[0-?]*[ -\/]*[@-~])'
def capture_escaped_line():
    y = tmux.get_variable('cursor_y')
    line = tmux.capture_pane(start=y, join=True, dump=True, escape=True).rstrip()
    splits = re.split(ESCAPE_CODE_RE, line)
    return line, splits

def is_escape_code(s):
    return re.match(ESCAPE_CODE_RE, s)

def named_group(name, regex):
    return '(?P<{}>{})'.format(name, regex)

def get_current():
    pane = tmux.capture_lines()
    for cfg in config.context_configs:
        for pattern in cfg['patterns']:
            search_pattern = '(?:^|\n)' + pattern + '(?: (?P<cmdline>.*))?$'
            m = re.search(search_pattern, pane)
            if m:
                cmd = (m.group('cmdline') or '').strip()
                log.info(
                    'Matched context "{}" with pattern "{}" and command "{}"',
                    cfg['name'], pattern, cmd)
                return Context(cfg=cfg, pattern=pattern, cmd_line=cmd, match=m)
    return None

def finditer_prompts(text, pattern):
    search_pattern = '(?:^|\n)' + named_group('pattern', pattern)
    for match in re.finditer(search_pattern, text):
        yield common.Namespace(
            start=match.start('pattern'), end=match.end('pattern'))
