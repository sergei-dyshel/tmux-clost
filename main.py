#!/usr/bin/env python

import sys
import traceback
import argparse
import os.path
import os

import common
import log
import tmux
import setup
import history

def bind_keys(args):
    pass

def save_to_history(args):
    config = common.get_config()
    ctx, _, cmd = common.get_context(config, silent=True)
    tmux.send_keys(['Enter'])
    if ctx is None:
        return

    log.info('Saving command "{}"', cmd)
    if cmd:
        history.save_to_history(ctx['name'], cmd)

def insert_snippet(args):
    config = common.get_config()
    ctx, _, _ = common.get_context(config)

    snippets_dir = common.get_config_var('snippets_dir', mandatory=True)
    ctx_snippets_dir = os.path.join(snippets_dir, ctx['name'])
    if not os.path.isdir(ctx_snippets_dir):
        return
    snippet_names = os.listdir(ctx_snippets_dir)

    snippet_name = setup.run_fzf('\n'.join(snippet_names))
    if not snippet_name:
        return

    with open(os.path.join(ctx_snippets_dir, snippet_name), 'rb+') as f:
        tmux.insert_text(f.read()[:-1])


def copy_output(args):
    import copy_output
    copy_output.main(args)

def handle_cmd(args):
    try:
        args.handler(args)
    except BaseException as exc:
        if sys.stdin.isatty():
            # executed manually by user
            raise
        else:
            # executed by tmux

            log.error(traceback.format_exc())
            msg = 'Clost: failed with {}: {}'.format(exc.__class__.__name__,
                                                     exc)
            ERROR_TIMEOUT = 5000
            tmux.display_message(msg, ERROR_TIMEOUT)

def main():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(title='Commands')

    bind_keys_parser = subparsers.add_parser('bind_keys')
    bind_keys_parser.set_defaults(handler=bind_keys)

    save_to_history_parser = subparsers.add_parser('save_to_history')
    save_to_history_parser.set_defaults(handler=save_to_history)

    insert_snippet_parser = subparsers.add_parser('insert_snippet')
    insert_snippet_parser.set_defaults(handler=insert_snippet)

    copy_output_parser = subparsers.add_parser('copy_output')
    copy_output_parser.set_defaults(handler=copy_output)

    args = parser.parse_args()
    handle_cmd(args)

if __name__ == '__main__':
    common.wrap_main(main)
