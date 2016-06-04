#!/usr/bin/env python

import tmux
import common
import history
import utils
import setup

def main(argv):
    config = common.get_config()
    ctx_name, ctx_conf = common.get_context(config)

    all_history = history.load_history(ctx_name)
    line = setup.run_fzf(all_history)
    if line:
        tmux.insert_text(line)

if __name__ == '__main__':
    common.wrap_main(main)
