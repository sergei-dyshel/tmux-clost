import shlex

import common

class Expander(object):
    def __init__(self, cmd, aliases):
        self.cmd = cmd.strip()
        self.aliases = aliases.copy()

    def _try(self):
        if not self.aliases or not self.cmd:
            raise StopIteration
        parts = self.cmd.split(' ', 1)
        alias = parts[0]
        rest = '' if len(parts) == 1 else parts[1]
        if alias not in self.aliases:
            raise StopIteration

        # 'pop' is to prevent recursive expansion of aliases of type df='df -h'
        exp = self.aliases.pop(alias)
        try:
            exp.format()
            self.cmd = exp + ' ' + rest
        except IndexError:
            argv = shlex.split(self.cmd)
            self.cmd = exp.format(*argv[1:])

    def run(self):
        for _ in xrange(10):
            try:
                self._try()
            except StopIteration:
                break
        return self.cmd


def expand(cmd, ctx):
    return Expander(cmd, ctx.get('aliases', {})).run()





