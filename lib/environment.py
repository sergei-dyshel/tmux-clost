import os.path
import os
import argparse
import string
import platform
import __main__

from . import tmux, log


_VAR_DEFS = [('work_dir', '~/.tmux-clost', 'Working directory'),
             ('config_file', '${work_dir}/config.yml',
              'User YAML configuration'),
             ('history_dir', '${work_dir}/history',
              'Directory with history files'),
             ('snippets_dir', '${work_dir}/snippets',
              'Directory with snippets')]

def mkdir(path):
    if not os.path.isdir(path):
        os.makedirs(path)


class Environment(object):
    exec_path = os.path.abspath(__main__.__file__)
    src_dir = os.path.dirname(os.path.abspath(__main__.__file__))
    vars = dict(hostname=platform.node())

    def temp_file_path(self, name):
        tmp_dir = os.path.join(self.vars['work_dir'], 'tmp')
        mkdir(tmp_dir)
        return os.path.join(tmp_dir, name)

    @classmethod
    def add_args(cls, parser):
        for name, default, help in _VAR_DEFS:
            arg_name = '--' + name.replace('_', '-')
            arg_help = '{} (default: {})'.format(help, default)
            meta = ('DIR' if name.endswith('_dir') else 'FILE'
                    if name.endswith('_file') else None)
            parser.add_argument(arg_name, metavar=meta, help=arg_help)

    def _expand_path(self, path):
        path = os.path.expanduser(path)
        return os.path.abspath(string.Template(path).substitute(self.vars))

    def init(self, args):
        arg_vars = vars(args)
        for name, default, _ in _VAR_DEFS:
            val = None
            env_name = 'CLOST_' + name.upper()
            if arg_vars[name] is not None:
                val = os.path.abspath(arg_vars[name])
            if not val and env_name in os.environ:
                    val = os.environ[env_name]
            if not val:
                val = tmux.get_option(name, clost=True)
            if not val:
                val = tmux.get_env(env_name)
            if not val:
                val = self._expand_path(default)
            self.vars[name] = val

    def dump(self):
        log.info('Environment:')
        for name, _, _ in _VAR_DEFS:
            log.info('{} = {}'.format(name, self.vars[name]))


env = Environment()
