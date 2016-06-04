#!/usr/bin/env python

import tmux
import common
import setup
import os.path
import os

def main(argv):
    config = common.get_config()
    ctx_name, ctx_conf = common.get_context(config)

    snippets_dir = common.get_config_var('snippets_dir', mandatory=True)
    ctx_snippets_dir = os.path.join(snippets_dir, ctx_name)
    if not os.path.isdir(ctx_snippets_dir):
        return
    snippet_names = os.listdir(ctx_snippets_dir)

    setup.unbind_enter()
    snippet_name = setup.run_fzf('\n'.join(snippet_names))
    if not snippet_name:
        return

    with open(os.path.join(ctx_snippets_dir, snippet_name), 'rb+') as f:
        tmux.insert_text(f.read()[:-1])

if __name__ == '__main__':
    common.wrap_main(main)

