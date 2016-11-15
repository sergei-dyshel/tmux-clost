import os.path
import os
import __main__
import argparse
import string

def expand_path(path):
    if not path:
        return path
    path = os.path.expanduser(path)
    return string.Template(path).substitute(os.environ, **variables)


def mkdir_p(path):
    try:
        os.makedirs(path)
    except OSError as e:
        if 'File exists' not in str(e):
            raise

def get_env_name(var_name):
    return 'CLOST_' + var_name.upper()

VARS = [
    ('main_dir', os.path.dirname(os.path.abspath(__main__.__file__)),
     'Directory with source code'),
    ('work_dir', '~/.tmux-clost', 'Working directory'),
    # ('log_file', '$CLOST_WORK_DIR/all.log', 'Log file path'),
    ('tmp_dir', '$CLOST_WORK_DIR/tmp', 'Directory for temporary files'),
    ('config_file', '$CLOST_WORK_DIR/config.yml', 'User YAML configuration'),
    ('snippets_dir', '$CLOST_WORK_DIR/snippets', 'Directory with snippets'),
    ('history_dir', '$CLOST_WORK_DIR/history', 'Directory where history saved'),
]

def add_args(parser):
    for name, default, help in VARS:
        arg_name = '--' + name.replace('_', '-')
        arg_help = '{} (default: ${} or {})'.format(
            help, get_env_name(name), default)
        meta = ('DIR' if name.endswith('_dir') else 'FILE'
                if name.endswith('_file') else None)
        parser.add_argument(arg_name, metavar=meta, help=arg_help)

def temp_file(name):
    return os.path.join(get_var('tmp_dir'), name)


# TODO: use just 'variables' instead
def get_var(var_name):
    global variables
    return  variables[var_name]

variables = {}

def configure(args):
    arg_vars = vars(args)
    for name, default, _ in VARS:
        env = get_env_name(name)
        val = (arg_vars[name] or os.environ.get(
            env, expand_path(default)))
        os.environ[env] = val
        if name.endswith('_dir'):
            mkdir_p(val)
        global variables
        variables[name] = val









