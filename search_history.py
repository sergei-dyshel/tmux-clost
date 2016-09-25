#!/usr/bin/env python

import tmux
import common
import history
import utils
import setup

def main(argv):
    config = common.get_config()
    ctx, _, _ = common.get_context(config)

    all_history = history.load_history(ctx['name'])
    line = setup.run_fzf(all_history)
    if line:
        tmux.insert_text(line)

if __name__ == '__main__':
    common.wrap_main(main)
