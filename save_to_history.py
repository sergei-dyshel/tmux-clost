#!/usr/bin/env python

import history
import common
import tmux

def main(argv):
    config = common.get_config()
    ctx_name, ctx_conf = common.get_context(config, silent=True)
    if ctx_name is None:
        tmux.send_keys(['Enter'])
        return

    patterns = ctx_conf['patterns']
    cmd = common.get_prompt_input(config, patterns[-1])
    tmux.send_keys(['Enter'])
    common.log_info('Saving command "{}"', cmd)
    if cmd:
        history.save_to_history(ctx_name, cmd)

if __name__ == '__main__':
    common.wrap_main(main)
