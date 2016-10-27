import os.path
import os
import argparse
import shlex
import sys

import common
import log
import tmux
import setup
import history
import output
import utils
import alias

from . import environment, config

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

@cmd()
def init():
    path = tmux.get_env('PATH')
    plugin_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
    if plugin_dir not in path:
        tmux.set_env('PATH', plugin_dir + ':' + path)
    setup.unbind_enter()
    setup.bind_enter()

@cmd()
def help():
    for name in list_names():
        params = getattr(get(name), PARAMS_ATTR)
        if hasattr(params, 'key'):
            print params.key, name


@cmd()
def expand_alias():
    ctx, _, cmd = common.get_context()
    exp = alias.expand(cmd, ctx)
    tmux.replace_cmd_line(exp)


@cmd()
def edit_cmd():
    ctx, _, cmd = common.get_context()
    cmd_file = common.get_temp_file('cmd.txt')
    with open(cmd_file, 'w') as f:
        f.write(cmd)
    # editor = common.get_config()['editor']
    # editor = environment.expand_path(config.get_option('editor'))
    editor = config.get_option('editor')
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
    ctx, _, cmd = common.get_context(silent=True)
    try:
        newcmd = alias.expand(cmd, ctx)
        if newcmd.strip() != cmd.strip():
            cmd = newcmd
            tmux.replace_cmd_line(cmd)
    except Exception:
        pass
    tmux.send_keys(['Enter'])
    if ctx is None:
        return
    if cmd:
        log.info('Saving command "{}"', cmd)
        history.save_to_history(ctx['name'], cmd)

@cmd()
def show_context():
    ctx, pattern, cmd = common.get_context()
    print '''tmux-clost current context:
    CONTEXT: {ctx[name]}
    PATTERN: {pattern}
    CMD: {cmd}
    '''.format(**locals())


@cmd()
def insert_snippet():
    ctx, _, _ = common.get_context()

    snippets_dir = environment.var.snippets_dir
    ctx_snippets_dir = os.path.join(snippets_dir, ctx['name'])
    if not os.path.isdir(ctx_snippets_dir):
        return
    snippet_names = os.listdir(ctx_snippets_dir)

    snippet_name = utils.select_split(snippet_names)
    if not snippet_name:
        return

    with open(os.path.join(ctx_snippets_dir, snippet_name), 'rb+') as f:
        tmux.insert_text(f.read()[:-1])

@cmd()
def copy_output():
    ctx, pattern, _ = common.get_context()

    out = output.get(ctx, pattern)

    # save_path = os.path.join(common.get_workdir(), 'output.txt')
    # with open(save_path, 'w') as f:
    #     f.write(out)
    # output.file_to_clipboard(save_path)
    output.copy_to_clipboard(out)

    num_lines = out.count('\n') + 1
    tmux.display_message('Copied {} lines (context: {})'.format(
        num_lines, ctx['name']))

@cmd()
def path_picker():
    ctx, pattern, _ = common.get_context()
    out = output.get(ctx, pattern)
    save_path = os.path.join(environment.var.tmp_dir, 'output.txt')
    with open(save_path, 'w') as f:
        f.write(out)
    pane_id = tmux.get_variable('pane_id')
    helper = os.path.join(environment.var.main_dir, 'scripts', 'fpp_helper.sh')
    utils.run_in_split_window('cat {} | /home/sergei/opt/fpp/fpp -nfc -ai -ni -c {} {}'.format(
        save_path, helper, pane_id))

@cmd()
def search_history():
    ctx, _, _ = common.get_context()

    line = utils.select_split_pipe('cat {}'.format(
        history.get_history_path(ctx['name'])))
    if line:
        tmux.insert_text(line)



