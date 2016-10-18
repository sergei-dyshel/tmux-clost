import os.path
import os
import argparse
import shlex

import common
import log
import tmux
import setup
import history
import output
import utils

PARAMS_ATTR = '__clost__cmd__'
KEY_TABLE = 'clost'


def cmd(**kwargs):
    def decorator(func):
        setattr(func, PARAMS_ATTR, argparse.Namespace(**kwargs))
        return func
    return decorator

def list_names():
    return [name for name, func in globals().iteritems()
            if hasattr(func, PARAMS_ATTR)]

def get(name):
    return globals()[name]

@cmd(key='b')
def bind_keys():
    common.config = None # TODO: reload config properly
    setup.unbind_enter()
    setup.bind_enter()
    cfg = common.get_config()
    if 'root_prefix' in cfg:
        tmux.bind_key(
            cfg['root_prefix'], ['switch-client', '-T', KEY_TABLE],
            no_prefix=True)

    tmux.unbind_key(all=True, key_table=KEY_TABLE)
    for name in list_names():
        params = getattr(get(name), PARAMS_ATTR)
        if hasattr(params, 'key'):
            setup.bind_key_to_cmd(params.key, name, key_table=KEY_TABLE)

@cmd(key='h')
def help():
    for name in list_names():
        params = getattr(get(name), PARAMS_ATTR)
        if hasattr(params, 'key'):
            print params.key, name

@cmd(key='a')
def expand_alias():
    ctx, _, cmd = common.get_context()
    if 'aliases' not in ctx:
        raise common.Error('No aliases defined for context "{}"', ctx['name'])
    argv = shlex.split(cmd)
    if not argv:
        raise common.Error('Empty command line')
    alias = argv[0].strip()
    if alias not in ctx['aliases']:
        raise common.Error('Alias "{}" not defined for context "{}"', alias,
                           ctx['name'])
    alias_def = ctx['aliases'][alias]
    exp = alias_def.format(*argv[1:])
    tmux.send_keys(['C-e', 'C-u'])
    tmux.send_keys([exp], literally=True)

@cmd(key='e')
def edit_cmd():
    ctx, _, cmd = common.get_context()
    cmd_file = common.get_temp_file('cmd.txt')
    with open(cmd_file, 'w') as f:
        f.write(cmd)
    editor = common.get_config()['editor']
    res = utils.run_in_split_window('{} {}'.format(editor, cmd_file))
    if res != 0:
        log.info(
            'Editing command line was cancelled (editor exited with status {})',
            res)
        return
    with open(cmd_file) as f:
        tmux.replace_cmd_line(f.read().strip())


@cmd()
def save_to_history():
    if (tmux.get_variable('pane_current_command').strip() not in
        ['ssh', 'screen', 'tmux'] and
            tmux.get_variable('alternate_on').strip() == '1'):
        tmux.send_keys(['Enter'])
        log.debug('Not intercepting "Enter" on alternate screen')
        return

    ctx, _, cmd = common.get_context(silent=True)
    tmux.send_keys(['Enter'])
    if ctx is None:
        return
    if cmd:
        log.info('Saving command "{}"', cmd)
        history.save_to_history(ctx['name'], cmd)

@cmd(key='x')
def show_context():
    ctx, pattern, cmd = common.get_context()
    print '''tmux-clost current context:
    CONTEXT: {ctx[name]}
    PATTERN: {pattern}
    CMD: {cmd}
    '''.format(**locals())


@cmd(key='u')
def insert_snippet():
    ctx, _, _ = common.get_context()

    snippets_dir = common.get_config_var('snippets_dir', mandatory=True)
    ctx_snippets_dir = os.path.join(snippets_dir, ctx['name'])
    if not os.path.isdir(ctx_snippets_dir):
        return
    snippet_names = os.listdir(ctx_snippets_dir)

    snippet_name = utils.select_split(snippet_names)
    if not snippet_name:
        return

    with open(os.path.join(ctx_snippets_dir, snippet_name), 'rb+') as f:
        tmux.insert_text(f.read()[:-1])

@cmd(key='c')
def copy_output():
    ctx, pattern, _ = common.get_context()

    out = output.get(ctx, pattern)
    save_path = os.path.join(common.get_workdir(), 'output.txt')

    with open(save_path, 'w') as f:
        f.write(out)

    output.file_to_clipboard(save_path)

    num_lines = out.count('\n') + 1
    tmux.display_message('Copied {} lines (context: {})'.format(
        num_lines, ctx['name']))

@cmd(key='r')
def search_history():
    ctx, _, _ = common.get_context()

    all_history = history.load_history(ctx['name'])
    line = utils.select_split(all_history)
    if line:
        tmux.insert_text(line)



